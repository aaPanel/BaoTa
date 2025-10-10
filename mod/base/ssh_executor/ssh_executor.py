from __future__ import annotations

import os
import stat
from typing import Optional, Tuple, Callable, Union, Dict, Any, Iterator
import time
import io
import math

import paramiko
from dataclasses import dataclass
from .rate_limiter import RateLimiter, ProgressTracker


@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


class SSHExecutor:
    """
    High-level SSH executor wrapping Paramiko for command execution and SFTP upload.

    Usage:
        with SSHExecutor(host, user, password=...) as ssh:
            code, out, err = ssh.run("uname -a")
            ssh.upload("./local.txt", "/tmp/remote.txt")
    """

    def __init__(
            self,
            host: str,
            username: str,
            port: int = 22,
            password: Optional[str] = None,
            key_file: Optional[str] = None,
            passphrase: Optional[str] = None,
            key_data: Optional[str] = None,
            timeout: Optional[int] = None,
            strict_host_key_checking: bool = False,
            allow_agent: bool = False,
            look_for_keys: bool = False,
            threading_mod: bool = False, # 线程模式，默认为False，当线程模式，会在每次获取sftp客户端时重新获取，
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.passphrase = passphrase
        self.key_data = key_data
        self.timeout = timeout or 20
        self.strict_host_key_checking = strict_host_key_checking
        self.allow_agent = allow_agent
        self.look_for_keys = look_for_keys
        self._client: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None
        self._threading_mod = threading_mod

    def open(self) -> None:
        if self._client is not None:
            return
        client = paramiko.SSHClient()
        if self.strict_host_key_checking:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: Dict[str, Any] = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
            "look_for_keys": self.look_for_keys,
            "allow_agent": self.allow_agent,
        }
        if self.timeout is not None:
            connect_kwargs.update({
                "timeout": self.timeout,
                "banner_timeout": self.timeout,
                "auth_timeout": self.timeout,
            })
        if self.password:
            connect_kwargs["password"] = self.password

        if self.key_file or self.key_data:
            pkey = self._load_private_key(self.key_file, self.key_data, self.passphrase)
            connect_kwargs["pkey"] = pkey

        try:
            client.connect(**connect_kwargs)
        except Exception as e:
            client.close()
            raise RuntimeError(f"SSH connection failed: {e}")

        self._client = client

    def close(self) -> None:
        if self._sftp is not None:
            try:
                self._sftp.close()
            finally:
                self._sftp = None
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None

    def __enter__(self) -> "SSHExecutor":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def run(self, command: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        client = self._require_client()
        try:
            effective_timeout = timeout if timeout is not None else self.timeout
            stdin, stdout, stderr = client.exec_command(command, timeout=effective_timeout)
            exit_status = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            return exit_status, out, err
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {e}")

    def upload(
            self,
            local_path: str,
            remote_path: str,
            rate_limit: Optional[int] = None,
            progress_callback: Optional[Callable[[int, int], None]] = None,
            resume: bool = False,
            rate_algorithm: str = "token_bucket",
            burst_capacity: Optional[int] = None,
            rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        """
        Upload a file via SFTP with optional rate limiting and resume support.

        Args:
            local_path: Local file path
            remote_path: Remote destination path
            rate_limit: Rate limit in bytes per second (None = no limit)
            progress_callback: Callback(transferred_bytes, total_bytes) for progress updates
            resume: Whether to resume upload if remote file exists and is smaller.
                   WARNING: Only checks file size, no content verification. Use with caution.
            rate_algorithm: Rate limiting algorithm ("token_bucket" or "leaky_bucket")
            burst_capacity: For token bucket, maximum burst capacity in bytes
            rate_limiter: External RateLimiter instance for unified control across multiple transfers
        """
        expanded_local = os.path.expanduser(local_path)
        if not os.path.isfile(expanded_local):
            raise FileNotFoundError(f"Local file not found: {expanded_local}")

        local_size = os.path.getsize(expanded_local)
        resume_offset = 0

        if resume:
            sftp = None
            try:
                sftp = self.get_sftp()
                remote_stat = sftp.stat(remote_path)
                if remote_stat.st_size < local_size:
                    resume_offset = remote_stat.st_size
                    if progress_callback:
                        progress_callback(resume_offset, local_size)
            except FileNotFoundError:
                pass
            except Exception:
                pass
            finally:
                if self._threading_mod and sftp:
                    sftp.close()

        sftp = None
        try:
            sftp = self.get_sftp()
            # Use external rate limiter if provided, otherwise create new one
            if rate_limiter is None:
                rate_limiter = RateLimiter(rate_limit, rate_algorithm, burst_capacity)
            progress_tracker = ProgressTracker(progress_callback)

            # Use chunked transfer for better control
            self._upload_chunked(sftp, expanded_local, remote_path, resume_offset, rate_limiter, progress_tracker)

        except Exception as e:
            raise RuntimeError(f"SFTP upload failed: {e}")
        finally:
            if self._threading_mod and sftp:
                sftp.close()

    def _ensure_remote_dir(self, sftp, path):
        try:
            sftp.stat(path)
        except FileNotFoundError:
            self._create_remote_dir_recursive(sftp, path)

    @staticmethod
    def _create_remote_dir_recursive(sftp, path):
        dirs = [d for d in path.split('/') if d]
        current = ''
        for d in dirs:
            current += '/' + d
            try:
                sftp.stat(current)
            except FileNotFoundError:
                sftp.mkdir(current)

    def _upload_chunked(
            self,
            sftp: paramiko.SFTPClient,
            local_path: str,
            remote_path: str,
            resume_offset: int,
            rate_limiter: Optional[RateLimiter] = None,
            progress_tracker: Optional[ProgressTracker] = None,
    ) -> None:
        """Upload file in chunks with optional rate limiting and progress tracking."""
        local_size = os.path.getsize(local_path)
        chunk_size = 32768  # 32KB chunks
        transferred = resume_offset

        # Initialize components if provided
        if rate_limiter:
            rate_limiter.start()
        if progress_tracker:
            progress_tracker.start()

        with open(local_path, "rb") as local_file:
            if resume_offset > 0:
                local_file.seek(resume_offset)

            # 检查目录是否存在，不存在则创建
            self._ensure_remote_dir(sftp, os.path.dirname(remote_path))

            with sftp.file(remote_path, "ab" if resume_offset > 0 else "wb") as remote_file:
                while transferred < local_size:
                    chunk = local_file.read(chunk_size)
                    if not chunk:
                        break

                    # Apply rate limiting before transfer
                    if rate_limiter:
                        rate_limiter.wait_if_needed(len(chunk))

                    # Perform the actual transfer
                    remote_file.write(chunk)
                    transferred += len(chunk)

                    # Update progress after transfer
                    if progress_tracker:
                        progress_tracker.update(transferred, local_size)

        # Final progress update
        if progress_tracker:
            progress_tracker.finish(local_size)

    def download(
            self,
            remote_path: str,
            local_path: str,
            rate_limit: Optional[int] = None,
            progress_callback: Optional[Callable[[int, int], None]] = None,
            resume: bool = False,
            rate_algorithm: str = "token_bucket",
            burst_capacity: Optional[int] = None,
            rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        """
        Download a file via SFTP with optional rate limiting and resume support.

        Args:
            remote_path: Remote file path
            local_path: Local destination path
            rate_limit: Rate limit in bytes per second (None = no limit)
            progress_callback: Callback(transferred_bytes, total_bytes) for progress updates
            resume: Whether to resume download if local file exists and is smaller.
                   WARNING: Only checks file size, no content verification. Use with caution.
            rate_algorithm: Rate limiting algorithm ("token_bucket" or "leaky_bucket")
            burst_capacity: For token bucket, maximum burst capacity in bytes
            rate_limiter: External RateLimiter instance for unified control across multiple transfers
        """
        expanded_local = os.path.expanduser(local_path)
        resume_offset = 0

        sftp = None
        if resume and os.path.exists(expanded_local):
            local_size = os.path.getsize(expanded_local)
            try:
                sftp = self.get_sftp()
                remote_stat = sftp.stat(remote_path)
                if local_size < remote_stat.st_size:
                    resume_offset = local_size
                    if progress_callback:
                        progress_callback(resume_offset, remote_stat.st_size)
            except Exception:
                pass
            finally:
                if self._threading_mod and sftp:
                    sftp.close()

        try:
            sftp = self.get_sftp()
            # Use external rate limiter if provided, otherwise create new one
            if rate_limiter is None:
                rate_limiter = RateLimiter(rate_limit, rate_algorithm, burst_capacity)
            progress_tracker = ProgressTracker(progress_callback)

            # Use chunked transfer for better control
            self._download_chunked(sftp, remote_path, expanded_local, resume_offset, rate_limiter, progress_tracker)

        except Exception as e:
            raise RuntimeError(f"SFTP download failed: {e}")
        finally:
            if self._threading_mod and sftp:
                sftp.close()

    @staticmethod
    def _download_chunked(
            sftp,
            remote_path: str,
            local_path: str,
            resume_offset: int,
            rate_limiter: Optional[RateLimiter] = None,
            progress_tracker: Optional[ProgressTracker] = None,
    ) -> None:
        """Download file in chunks with optional rate limiting and progress tracking."""
        remote_size = sftp.stat(remote_path).st_size
        chunk_size = 32768  # 32KB chunks
        transferred = resume_offset

        # Initialize components if provided
        if rate_limiter:
            rate_limiter.start()
        if progress_tracker:
            progress_tracker.start()

        mode = "ab" if resume_offset > 0 else "wb"
        with open(local_path, mode) as local_file:
            with sftp.file(remote_path, "rb") as remote_file:
                if resume_offset > 0:
                    remote_file.seek(resume_offset)

                while transferred < remote_size:
                    # Apply rate limiting before transfer
                    if rate_limiter:
                        rate_limiter.wait_if_needed(chunk_size)

                    # Perform the actual transfer
                    chunk = remote_file.read(chunk_size)
                    if not chunk:
                        break

                    local_file.write(chunk)
                    transferred += len(chunk)

                    # Update progress after transfer
                    if progress_tracker:
                        progress_tracker.update(transferred, remote_size)

        # Final progress update
        if progress_tracker:
            progress_tracker.finish(remote_size)

    def _require_client(self) -> paramiko.SSHClient:
        if self._client is None:
            raise RuntimeError("SSH client is not connected. Call open() or use a with-context.")
        return self._client

    def get_sftp(self) -> paramiko.SFTPClient:
        if self._threading_mod:
            th_sftp = self._require_client().open_sftp()
            return th_sftp
        if self._sftp is None:
            self._sftp = self._require_client().open_sftp()
        return self._sftp

    @staticmethod
    def _load_private_key(
            key_file: Optional[str],
            key_data: Optional[str],
            passphrase: Optional[str],
    ) -> paramiko.PKey:
        """Load a private key by normalizing to key_data and parsing it.

        Priority is mutually exclusive by design: key_file > key_data.
        Supported types: RSA, DSS, ECDSA, Ed25519.
        """
        if not key_data and key_file:
            path = os.path.expanduser(key_file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    key_data = f.read()
            except Exception as e:
                raise RuntimeError(f"Failed to read private key file: {e}")

        if not key_data:
            raise RuntimeError("No private key provided")

        stream = io.StringIO(key_data)
        last_error: Optional[Exception] = None
        key_classes = [paramiko.RSAKey, paramiko.ECDSAKey, paramiko.Ed25519Key]
        if hasattr(paramiko, "DSSKey"):  # 兼容无DSSKey功能的paramiko版本
            key_classes.append(paramiko.DSSKey)
        for key_cls in key_classes:
            try:
                stream.seek(0)
                return key_cls.from_private_key(stream, password=passphrase)
            except paramiko.PasswordRequiredException:
                raise RuntimeError("Private key is encrypted; provide passphrase.")
            except Exception as e:
                last_error = e
        raise RuntimeError(f"Failed to load private key from data: {last_error}")

    def run_streaming(
            self,
            command: str,
            on_stdout: Optional[Callable[[bytes], None]] = None,
            on_stderr: Optional[Callable[[bytes], None]] = None,
            timeout: Optional[int] = None,
            read_chunk_size: int = 32768,
            poll_interval_sec: float = 0.05,
    ) -> int:
        """
        Execute a remote command and stream output chunks to callbacks to minimize memory usage.

        Returns the process exit status when the command completes.
        """
        client = self._require_client()
        transport = client.get_transport()
        if transport is None:
            raise RuntimeError("SSH transport is not available")

        effective_timeout = timeout if timeout is not None else self.timeout
        chan = transport.open_session(timeout=effective_timeout)
        chan.exec_command(command)

        start_time = time.time()

        try:
            while True:
                if chan.recv_ready():
                    data = chan.recv(read_chunk_size)
                    if data and on_stdout is not None:
                        on_stdout(data)
                if chan.recv_stderr_ready():
                    data = chan.recv_stderr(read_chunk_size)
                    if data and on_stderr is not None:
                        on_stderr(data)

                if chan.exit_status_ready() and not chan.recv_ready() and not chan.recv_stderr_ready():
                    break

                if effective_timeout is not None and (time.time() - start_time) > effective_timeout:
                    chan.close()
                    raise TimeoutError("Command execution timed out")

                time.sleep(poll_interval_sec)

            exit_code = chan.recv_exit_status()
            return exit_code
        finally:
            try:
                chan.close()
            except Exception:
                pass

    def execute_script_streaming(
            self,
            script_content: str,
            script_type: str = "shell",
            remote_dir: str = "/tmp",
            script_name: Optional[str] = None,
            timeout: Optional[int] = None,
            cleanup: bool = True,
            env_vars: Optional[Dict[str, str]] = None,
            on_stdout: Optional[Callable[[bytes], None]] = None,
            on_stderr: Optional[Callable[[bytes], None]] = None,
    ) -> int:
        """
        Execute a bash script with streaming output.
        
        Args:
            script_content: The bash script content to execute
            remote_dir: Remote directory to place the script (default: /tmp)
            script_name: Name for the script file (auto-generated if None)
            timeout: Command execution timeout in seconds
            cleanup: Whether to delete the script file after execution
            env_vars: Environment variables to set before script execution
            on_stdout: Callback to receive stdout chunks (bytes)
            on_stderr: Callback to receive stderr chunks (bytes)
            
        Returns:
            int: Exit code of the script execution
            
        Raises:
            RuntimeError: If script upload or execution fails
        """
        remote_script_path = self._prepare_script(script_content, remote_dir, script_name)

        try:
            command = self._build_command(remote_script_path, script_type, env_vars)
            return self.run_streaming(
                command,
                on_stdout=on_stdout,
                on_stderr=on_stderr,
                timeout=timeout,
            )
        finally:
            if cleanup:
                self._cleanup_script(remote_script_path)

    def execute_script_collect(
            self,
            script_content: str,
            script_type: str = "shell",
            remote_dir: str = "/tmp",
            script_name: Optional[str] = None,
            timeout: Optional[int] = None,
            cleanup: bool = True,
            env_vars: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """
        Execute a bash script and collect all output.
        
        Args:
            script_content: The bash script content to execute
            remote_dir: Remote directory to place the script (default: /tmp)
            script_name: Name for the script file (auto-generated if None)
            timeout: Command execution timeout in seconds
            cleanup: Whether to delete the script file after execution
            env_vars: Environment variables to set before script execution
            
        Returns:
            CommandResult: The execution result with exit_code, stdout, stderr
            
        Raises:
            RuntimeError: If script upload or execution fails
        """
        remote_script_path = self._prepare_script(script_content, remote_dir, script_name)

        try:
            command = self._build_command(remote_script_path, script_type, env_vars)
            code, out, err = self.run(command, timeout=timeout)
            return CommandResult(exit_code=code, stdout=out, stderr=err)
        finally:
            if cleanup:
                self._cleanup_script(remote_script_path)

    def execute_local_script_streaming(
            self,
            local_script_path: str,
            script_type: str = "shell",
            remote_dir: str = "/tmp",
            script_name: Optional[str] = None,
            timeout: Optional[int] = None,
            cleanup: bool = True,
            env_vars: Optional[Dict[str, str]] = None,
            on_stdout: Optional[Callable[[bytes], None]] = None,
            on_stderr: Optional[Callable[[bytes], None]] = None,
    ) -> int:
        """
        Execute a local bash script with streaming output.
        
        Args:
            local_script_path: Path to the local script file
            remote_dir: Remote directory to place the script (default: /tmp)
            script_name: Name for the script file (uses basename if None)
            timeout: Command execution timeout in seconds
            cleanup: Whether to delete the script file after execution
            env_vars: Environment variables to set before script execution
            on_stdout: Callback to receive stdout chunks (bytes)
            on_stderr: Callback to receive stderr chunks (bytes)
            
        Returns:
            int: Exit code of the script execution
            
        Raises:
            FileNotFoundError: If local script file not found
            RuntimeError: If script upload or execution fails
        """
        if not os.path.isfile(local_script_path):
            raise FileNotFoundError(f"Local script not found: {local_script_path}")

        if not script_name:
            script_name = os.path.basename(local_script_path)

        remote_script_path = f"{remote_dir.rstrip('/')}/{script_name}"

        # Upload the local script file via SFTP with LF normalization
        sftp = self.get_sftp()
        with open(local_script_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
        content_lf = content.replace("\r\n", "\n").replace("\r", "\n")
        with sftp.file(remote_script_path, "w") as remote_file:
            remote_file.write(content_lf.encode("utf-8"))

        try:
            command = self._build_command(remote_script_path, script_type, env_vars)
            return self.run_streaming(
                command,
                on_stdout=on_stdout,
                on_stderr=on_stderr,
                timeout=timeout,
            )
        finally:
            if cleanup:
                self._cleanup_script(remote_script_path)

    def execute_local_script_collect(
            self,
            local_script_path: str,
            script_type: str = "shell",
            remote_dir: str = "/tmp",
            script_name: Optional[str] = None,
            timeout: Optional[int] = None,
            cleanup: bool = True,
            env_vars: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """
        Execute a local bash script and collect all output.
        
        Args:
            local_script_path: Path to the local script file
            remote_dir: Remote directory to place the script (default: /tmp)
            script_name: Name for the script file (uses basename if None)
            timeout: Command execution timeout in seconds
            cleanup: Whether to delete the script file after execution
            env_vars: Environment variables to set before script execution
            
        Returns:
            CommandResult: The execution result with exit_code, stdout, stderr
            
        Raises:
            FileNotFoundError: If local script file not found
            RuntimeError: If script upload or execution fails
        """
        if not os.path.isfile(local_script_path):
            raise FileNotFoundError(f"Local script not found: {local_script_path}")

        if not script_name:
            script_name = os.path.basename(local_script_path)

        remote_script_path = f"{remote_dir.rstrip('/')}/{script_name}"

        # Upload the local script file via SFTP with LF normalization
        sftp = self.get_sftp()
        with open(local_script_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
        content_lf = content.replace("\r\n", "\n").replace("\r", "\n")
        with sftp.file(remote_script_path, "w") as remote_file:
            remote_file.write(content_lf.encode("utf-8"))

        try:
            command = self._build_command(remote_script_path, script_type, env_vars)
            code, out, err = self.run(command, timeout=timeout)
            return CommandResult(exit_code=code, stdout=out, stderr=err)
        finally:
            if cleanup:
                self._cleanup_script(remote_script_path)

    def _prepare_script(self, script_content: str, remote_dir: str, script_name: Optional[str]) -> str:
        """Prepare script by uploading content (LF normalized)."""
        if not script_name:
            import uuid
            script_name = f"script_{uuid.uuid4().hex[:8]}"

        remote_script_path = f"{remote_dir.rstrip('/')}/{script_name}"

        sftp = None
        try:
            # Upload script content directly via SFTP (normalize to LF)
            sftp = self.get_sftp()
            content_lf = script_content.replace("\r\n", "\n").replace("\r", "\n")
            with sftp.file(remote_script_path, "w") as remote_file:
                remote_file.write(content_lf.encode("utf-8"))
        except:
            pass
        finally:
            if sftp and self._threading_mod:
                sftp.close()

        return remote_script_path

    @staticmethod
    def _build_command(
            remote_script_path: str,
            script_type: str = "shell",
            env_vars: Optional[Dict[str, str]] = None) -> str:
        """Build the command string with environment variables."""
        env_string = ""
        if env_vars:
            env_pairs = [f"{k}='{v}'" for k, v in env_vars.items()]
            env_string = " ".join(env_pairs) + " "

        if script_type == "shell":
            return f"{env_string}bash {remote_script_path}"
        elif script_type == "python":
            get_py_bin = "pyBin=$(which python3 2> /dev/null || which python 2> /dev/null || echo 'python')"
            py_info = "echo ""; echo \"当前python环境:${pyBin} $(${pyBin} -c 'import sys,platform;print(sys.version.split()[0],platform.platform())')\""
            cmd = "%s;${pyBin} %s; ret=$?; [ $ret -eq 0 ] && exit $ret; %s;exit $ret;" % (
                get_py_bin, remote_script_path, py_info
            )
            return cmd
        else:
            raise ValueError("Invalid script type")

    def _cleanup_script(self, remote_script_path: str) -> None:
        """Clean up the remote script file via SFTP without invoking shell."""
        sftp = None
        try:
            sftp = self.get_sftp()
            # Ensure path exists before removal
            try:
                sftp.stat(remote_script_path)
            except FileNotFoundError:
                return
            sftp.remove(remote_script_path)
        except Exception:
            # Swallow cleanup errors
            pass
        finally:
            if sftp and self._threading_mod:
                sftp.close()

    def path_exists(self, path: str) -> Tuple[bool, str]:
        """
        Check if a path exists on the remote server.

        Args:
            path: Path to check

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating whether the path exists and an error message
        """
        sftp = None
        try:
            sftp = self.get_sftp()
            try:
                sftp.stat(path)
                return True, ""
            except FileNotFoundError:
                return False, ""
        except Exception as e:
            return False, str(e)
        finally:
            if sftp and self._threading_mod:
                sftp.close()


    def create_dir(self, path: str):
        """
        Create a directory on the remote server.

        Args:
            path: Path to create

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating whether the directory was created successfully and an error message
        """
        sftp = None
        try:
            sftp = self.get_sftp()
            self._ensure_remote_dir(sftp, path)
            return True, ""
        except Exception as e:
            return False, str(e)
        finally:
            if sftp and self._threading_mod:
                return sftp.close()

    def path_info(self, path: str) -> Dict:
        """
        Get information about a path on the remote server.

        Args:
            path: Path to get information about

        Returns:
            Dict: A dictionary containing information about the path, including path, isdir, size, mtime, mode, uid, gid, and exists
        """
        sftp = None
        not_found = {"path": path,"isdir": False,"size": 0,"mtime": 0,"mode": 0,"uid": 0,"gid": 0, "exists": False}
        try:
            sftp = self.get_sftp()
            info = sftp.stat(path)
            return {
                "path": path,
                "isdir": stat.S_ISDIR(info.st_mode),
                "size": info.st_size,
                "mtime": info.st_mtime,
                "mode": info.st_mode,
                "uid": info.st_uid,
                "gid": info.st_gid,
                "exists": True
            }
        except FileNotFoundError:
            return not_found
        except:
            return not_found
        finally:
            if sftp and self._threading_mod:
                sftp.close()

