# -*- coding: utf-8 -*-

"""
oss2.xml_utils
~~~~~~~~~~~~~~

XML处理相关。

主要包括两类接口：
    - parse_开头的函数：用来解析服务器端返回的XML
    - to_开头的函数：用来生成发往服务器端的XML

"""
import logging
import xml.etree.ElementTree as ElementTree

from .models import (SimplifiedObjectInfo,
                     SimplifiedBucketInfo,
                     PartInfo,
                     MultipartUploadInfo,
                     LifecycleRule,
                     LifecycleExpiration,
                     CorsRule,
                     LiveChannelInfoTarget,
                     LiveChannelInfo,
                     LiveRecord,
                     LiveChannelVideoStat,
                     LiveChannelAudioStat,
                     Owner,
                     AccessControlList,
                     AbortMultipartUpload,
                     StorageTransition,
                     Tagging,
                     TaggingRule,
                     ServerSideEncryptionRule,
                     ListObjectVersionsResult,
                     ObjectVersionInfo,
                     DeleteMarkerInfo,
                     BatchDeleteObjectVersionResult,
                     BucketWebsite,
                     RoutingRule,
                     Condition,
                     ConditionInlcudeHeader,
                     Redirect,
                     RedirectMirrorHeaders,
                     MirrorHeadersSet,
                     REDIRECT_TYPE_MIRROR,
                     REDIRECT_TYPE_EXTERNAL,
                     REDIRECT_TYPE_INTERNAL,
                     REDIRECT_TYPE_ALICDN,
                     NoncurrentVersionStorageTransition,
                     NoncurrentVersionExpiration,
                     AsyncFetchTaskConfiguration)

from .select_params import (SelectJsonTypes, SelectParameters)

from .compat import urlunquote, to_unicode, to_string
from .utils import iso8601_to_unixtime, date_to_iso8601, iso8601_to_date
from . import utils
import base64
from .exceptions import SelectOperationClientError

logger = logging.getLogger(__name__)

def _find_tag(parent, path):
    child = parent.find(path)
    if child is None:
        raise RuntimeError("parse xml: " + path + " could not be found under " + parent.tag)

    if child.text is None:
        return ''

    return to_string(child.text)


def _find_bool(parent, path):
    text = _find_tag(parent, path)
    if text == 'true':
        return True
    elif text == 'false':
        return False
    else:
        raise RuntimeError("parse xml: value of " + path + " is not a boolean under " + parent.tag)


def _find_int(parent, path):
    return int(_find_tag(parent, path))


def _find_object(parent, path, url_encoded):
    name = _find_tag(parent, path)
    if url_encoded:
        return urlunquote(name)
    else:
        return name


def _find_all_tags(parent, tag):
    return [to_string(node.text) or '' for node in parent.findall(tag)]


def _is_url_encoding(root):
    node = root.find('EncodingType')
    if node is not None and to_string(node.text) == 'url':
        return True
    else:
        return False


def _node_to_string(root):
    return ElementTree.tostring(root, encoding='utf-8')


def _add_node_list(parent, tag, entries):
    for e in entries:
        _add_text_child(parent, tag, e)


def _add_text_child(parent, tag, text):
    ElementTree.SubElement(parent, tag).text = to_unicode(text)

def _add_node_child(parent, tag):
    return ElementTree.SubElement(parent, tag)

def parse_list_objects(result, body):
    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)
    result.is_truncated = _find_bool(root, 'IsTruncated')
    if result.is_truncated:
        result.next_marker = _find_object(root, 'NextMarker', url_encoded)

    for contents_node in root.findall('Contents'):
        result.object_list.append(SimplifiedObjectInfo(
            _find_object(contents_node, 'Key', url_encoded),
            iso8601_to_unixtime(_find_tag(contents_node, 'LastModified')),
            _find_tag(contents_node, 'ETag').strip('"'),
            _find_tag(contents_node, 'Type'),
            int(_find_tag(contents_node, 'Size')),
            _find_tag(contents_node, 'StorageClass')
        ))

    for prefix_node in root.findall('CommonPrefixes'):
        result.prefix_list.append(_find_object(prefix_node, 'Prefix', url_encoded))

    return result


def parse_list_buckets(result, body):
    root = ElementTree.fromstring(body)

    if root.find('IsTruncated') is None:
        result.is_truncated = False
    else:
        result.is_truncated = _find_bool(root, 'IsTruncated')

    if result.is_truncated:
        result.next_marker = _find_tag(root, 'NextMarker')

    for bucket_node in root.findall('Buckets/Bucket'):
        result.buckets.append(SimplifiedBucketInfo(
            _find_tag(bucket_node, 'Name'),
            _find_tag(bucket_node, 'Location'),
            iso8601_to_unixtime(_find_tag(bucket_node, 'CreationDate')),
            _find_tag(bucket_node, 'ExtranetEndpoint'),
            _find_tag(bucket_node, 'IntranetEndpoint'),
            _find_tag(bucket_node, 'StorageClass')
        ))

    return result


def parse_init_multipart_upload(result, body):
    root = ElementTree.fromstring(body)
    result.upload_id = _find_tag(root, 'UploadId')

    return result


def parse_list_multipart_uploads(result, body):
    root = ElementTree.fromstring(body)

    url_encoded = _is_url_encoding(root)

    result.is_truncated = _find_bool(root, 'IsTruncated')
    result.next_key_marker = _find_object(root, 'NextKeyMarker', url_encoded)
    result.next_upload_id_marker = _find_tag(root, 'NextUploadIdMarker')

    for upload_node in root.findall('Upload'):
        result.upload_list.append(MultipartUploadInfo(
            _find_object(upload_node, 'Key', url_encoded),
            _find_tag(upload_node, 'UploadId'),
            iso8601_to_unixtime(_find_tag(upload_node, 'Initiated'))
        ))

    for prefix_node in root.findall('CommonPrefixes'):
        result.prefix_list.append(_find_object(prefix_node, 'Prefix', url_encoded))

    return result


def parse_list_parts(result, body):
    root = ElementTree.fromstring(body)

    result.is_truncated = _find_bool(root, 'IsTruncated')
    result.next_marker = _find_tag(root, 'NextPartNumberMarker')
    for part_node in root.findall('Part'):
        result.parts.append(PartInfo(
            _find_int(part_node, 'PartNumber'),
            _find_tag(part_node, 'ETag').strip('"'),
            size=_find_int(part_node, 'Size'),
            last_modified=iso8601_to_unixtime(_find_tag(part_node, 'LastModified'))
        ))

    return result


def parse_batch_delete_objects(result, body):
    if not body:
        return result 
    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)

    for deleted_node in root.findall('Deleted'):
        key = _find_object(deleted_node, 'Key', url_encoded)

        result.deleted_keys.append(key)

        versionid_node = deleted_node.find('VersionId')
        versionid = None
        if versionid_node is not None:
            versionid = _find_tag(deleted_node, 'VersionId')

        delete_marker_node = deleted_node.find('DeleteMarker')
        delete_marker = False
        if delete_marker_node is not None:
            delete_marker = _find_bool(deleted_node, 'DeleteMarker')

        marker_versionid_node = deleted_node.find('DeleteMarkerVersionId')
        delete_marker_versionid = ''
        if marker_versionid_node is not None:
            delete_marker_versionid = _find_tag(deleted_node, 'DeleteMarkerVersionId')
        result.delete_versions.append(BatchDeleteObjectVersionResult(key, versionid, delete_marker, delete_marker_versionid))

    return result


def parse_get_bucket_acl(result, body):
    root = ElementTree.fromstring(body)
    result.acl = _find_tag(root, 'AccessControlList/Grant')

    return result


def parse_get_object_acl(result, body):
    root = ElementTree.fromstring(body)
    result.acl = _find_tag(root, 'AccessControlList/Grant')

    return result


def parse_get_bucket_location(result, body):
    result.location = to_string(ElementTree.fromstring(body).text)
    return result


def parse_get_bucket_logging(result, body):
    root = ElementTree.fromstring(body)

    if root.find('LoggingEnabled/TargetBucket') is not None:
        result.target_bucket = _find_tag(root, 'LoggingEnabled/TargetBucket')

    if root.find('LoggingEnabled/TargetPrefix') is not None:
        result.target_prefix = _find_tag(root, 'LoggingEnabled/TargetPrefix')

    return result


def parse_get_bucket_stat(result, body):
    root = ElementTree.fromstring(body)

    result.storage_size_in_bytes = _find_int(root, 'Storage')
    result.object_count = _find_int(root, 'ObjectCount')
    result.multi_part_upload_count = _find_int(root, 'MultipartUploadCount')

    return result


def parse_get_bucket_info(result, body):
    root = ElementTree.fromstring(body)

    result.name = _find_tag(root, 'Bucket/Name')
    result.creation_date = _find_tag(root, 'Bucket/CreationDate')
    result.storage_class = _find_tag(root, 'Bucket/StorageClass')
    result.extranet_endpoint = _find_tag(root, 'Bucket/ExtranetEndpoint')
    result.intranet_endpoint = _find_tag(root, 'Bucket/IntranetEndpoint')
    result.location = _find_tag(root, 'Bucket/Location')
    result.owner = Owner(_find_tag(root, 'Bucket/Owner/DisplayName'), _find_tag(root, 'Bucket/Owner/ID'))
    result.acl = AccessControlList(_find_tag(root, 'Bucket/AccessControlList/Grant'))
    result.comment = _find_tag(root, 'Bucket/Comment')

    server_side_encryption = root.find("Bucket/ServerSideEncryptionRule")

    if server_side_encryption is None:
        result.bucket_encryption_rule = None
    else:
        result.bucket_encryption_rule = _parse_bucket_encryption_info(server_side_encryption)

    bucket_versioning = root.find('Bucket/Versioning')
    
    if bucket_versioning is None or bucket_versioning.text is None:
        result.versioning_status = None
    else:
        result.versioning_status = to_string(bucket_versioning.text)

    data_redundancy_type = root.find('Bucket/DataRedundancyType')
    if data_redundancy_type is None or data_redundancy_type.text is None:
        result.data_redundancy_type = None
    else:
        result.data_redundancy_type = to_string(data_redundancy_type.text)

    return result

def _parse_bucket_encryption_info(node):

    rule = ServerSideEncryptionRule()

    rule.sse_algorithm = _find_tag(node,"SSEAlgorithm")
    
    if rule.sse_algorithm == "None":
        rule.kms_master_keyid = None
        rule.sse_algorithm = None
        return rule

    kmsnode = node.find("KMSMasterKeyID")
    if kmsnode is None or kmsnode.text is None:
        rule.kms_master_keyid = None 
    else:
        rule.kms_master_keyid = to_string(kmsnode.text)

    return rule

def parse_get_bucket_referer(result, body):
    root = ElementTree.fromstring(body)

    result.allow_empty_referer = _find_bool(root, 'AllowEmptyReferer')
    result.referers = _find_all_tags(root, 'RefererList/Referer')

    return result

def parse_condition_include_header(include_header_node):
    key = _find_tag(include_header_node, 'Key')
    equals = _find_tag(include_header_node, 'Equals')
    include_header = ConditionInlcudeHeader(key, equals)

    return include_header

def parse_routing_rule_condition(condition_node):
    if condition_node.find('KeyPrefixEquals') is not None:
        key_prefix_equals = _find_tag(condition_node, 'KeyPrefixEquals')
    if condition_node.find('HttpErrorCodeReturnedEquals') is not None:
        http_err_code_return_equals = _find_int(condition_node, 'HttpErrorCodeReturnedEquals');
        
    include_header_list = []
    if condition_node.find('IncludeHeader') is not None:
        for include_header_node in condition_node.findall('IncludeHeader'):
            include_header = parse_condition_include_header(include_header_node)
            include_header_list.append(include_header)

    condition = Condition(key_prefix_equals, http_err_code_return_equals, include_header_list)

    return condition

def parse_mirror_headers(mirror_headers_node):
    if mirror_headers_node is None:
        return None
    
    pass_all = None
    if mirror_headers_node.find('PassAll') is not None:
        pass_all = _find_bool(mirror_headers_node, 'PassAll')
    
    pass_list = _find_all_tags(mirror_headers_node, 'Pass')
    remove_list = _find_all_tags(mirror_headers_node, 'Remove')
    set_list = []
    for set_node in mirror_headers_node.findall('Set'):
        key = _find_tag(set_node, 'Key')
        value = _find_tag(set_node, 'Value')
        mirror_headers_set = MirrorHeadersSet(key, value)
        set_list.append(mirror_headers_set)

    redirect_mirror_headers = RedirectMirrorHeaders(pass_all, pass_list, remove_list, set_list)

    return redirect_mirror_headers

def parse_routing_rule_redirect(redirect_node):
    redirect_type = None
    pass_query_string = None
    replace_key_with = None
    replace_key_prefix_with = None
    proto = None
    host_name = None
    http_redirect_code = None
    mirror_url = None
    mirror_url_slave = None
    mirror_url_probe = None
    mirror_pass_query_string = None
    mirror_check_md5 = None
    mirror_follow_redirect = None
    mirror_headers = None

    # common args
    redirect_type = _find_tag(redirect_node, 'RedirectType')

    if redirect_node.find('PassQueryString') is not None:
        pass_query_string = _find_bool(redirect_node, 'PassQueryString')

    # External, AliCDN
    if redirect_type in [REDIRECT_TYPE_EXTERNAL, REDIRECT_TYPE_ALICDN]:
        if redirect_node.find('Protocol') is not None:
            proto = _find_tag(redirect_node, 'Protocol')

        if redirect_node.find('HostName') is not None:
            host_name = _find_tag(redirect_node, 'HostName')

        if redirect_node.find('HttpRedirectCode') is not None:
            http_redirect_code = _find_int(redirect_node, 'HttpRedirectCode')

    # External, AliCDN, Internal
    if redirect_type in [REDIRECT_TYPE_EXTERNAL, REDIRECT_TYPE_ALICDN, REDIRECT_TYPE_INTERNAL]:
        if redirect_node.find('ReplaceKeyWith') is not None:
            replace_key_with = _find_tag(redirect_node, 'ReplaceKeyWith')
        if redirect_node.find('ReplaceKeyPrefixWith') is not None:
            replace_key_prefix_with = _find_tag(redirect_node, 'ReplaceKeyPrefixWith')

    # Mirror
    elif redirect_type == REDIRECT_TYPE_MIRROR:
        if redirect_node.find('MirrorURL') is not None:
            mirror_url = _find_tag(redirect_node, 'MirrorURL')

        if redirect_node.find('MirrorURLSlave') is not None:
            mirror_url_slave = _find_tag(redirect_node, 'MirrorURLSlave')

        if redirect_node.find('MirrorURLProbe') is not None:
            mirror_url_probe = _find_tag(redirect_node, 'MirrorURLProbe')

        if redirect_node.find('MirrorPassQueryString') is not None:
            mirror_pass_query_string = _find_bool(redirect_node, 'MirrorPassQueryString')

        if redirect_node.find('MirrorCheckMd5') is not None:
            mirror_check_md5 = _find_bool(redirect_node, 'MirrorCheckMd5')

        if redirect_node.find('MirrorFollowRedirect') is not None:
            mirror_follow_redirect = _find_bool(redirect_node, 'MirrorFollowRedirect')

        mirror_headers = parse_mirror_headers(redirect_node.find('MirrorHeaders'))

    redirect = Redirect(redirect_type=redirect_type, proto=proto, host_name=host_name, replace_key_with=replace_key_with, 
                    replace_key_prefix_with=replace_key_prefix_with, http_redirect_code=http_redirect_code, 
                    pass_query_string=pass_query_string, mirror_url=mirror_url,mirror_url_slave=mirror_url_slave, 
                    mirror_url_probe=mirror_url_probe, mirror_pass_query_string=mirror_pass_query_string, 
                    mirror_follow_redirect=mirror_follow_redirect, mirror_check_md5=mirror_check_md5, 
                    mirror_headers=mirror_headers)

    return redirect

def parse_get_bucket_website(result, body):
    root = ElementTree.fromstring(body)
    result.index_file = _find_tag(root, 'IndexDocument/Suffix')
    result.error_file = _find_tag(root, 'ErrorDocument/Key')

    if root.find('RoutingRules') is None:
        return result

    routing_rules_node = root.find('RoutingRules')

    for rule_node in routing_rules_node.findall('RoutingRule'):
        rule_num = _find_int(rule_node, 'RuleNumber')
        condition = parse_routing_rule_condition(rule_node.find('Condition'))
        redirect = parse_routing_rule_redirect(rule_node.find('Redirect'))
        rule = RoutingRule(rule_num, condition, redirect);
        result.rules.append(rule)

    return result


def parse_create_live_channel(result, body):
    root = ElementTree.fromstring(body)

    result.play_url = _find_tag(root, 'PlayUrls/Url')
    result.publish_url = _find_tag(root, 'PublishUrls/Url')

    return result


def parse_get_live_channel(result, body):
    root = ElementTree.fromstring(body)

    result.status = _find_tag(root, 'Status')
    result.description = _find_tag(root, 'Description')

    target = LiveChannelInfoTarget()
    target.type = _find_tag(root, 'Target/Type')
    target.frag_duration = _find_tag(root, 'Target/FragDuration')
    target.frag_count = _find_tag(root, 'Target/FragCount')
    target.playlist_name = _find_tag(root, 'Target/PlaylistName')

    result.target = target

    return result


def parse_list_live_channel(result, body):
    root = ElementTree.fromstring(body)

    result.prefix = _find_tag(root, 'Prefix')
    result.marker = _find_tag(root, 'Marker')
    result.max_keys = _find_int(root, 'MaxKeys')
    result.is_truncated = _find_bool(root, 'IsTruncated')
    
    if result.is_truncated:
        result.next_marker = _find_tag(root, 'NextMarker')

    channels = root.findall('LiveChannel')
    for channel in channels:
        tmp = LiveChannelInfo()
        tmp.name = _find_tag(channel, 'Name')
        tmp.description = _find_tag(channel, 'Description')
        tmp.status = _find_tag(channel, 'Status')
        tmp.last_modified = iso8601_to_unixtime(_find_tag(channel, 'LastModified'))
        tmp.play_url = _find_tag(channel, 'PlayUrls/Url')
        tmp.publish_url = _find_tag(channel, 'PublishUrls/Url')

        result.channels.append(tmp)

    return result


def parse_stat_video(video_node, video):
    video.width = _find_int(video_node, 'Width')
    video.height = _find_int(video_node, 'Height')
    video.frame_rate = _find_int(video_node, 'FrameRate')
    video.bandwidth = _find_int(video_node, 'Bandwidth')
    video.codec = _find_tag(video_node, 'Codec')


def parse_stat_audio(audio_node, audio):
    audio.bandwidth = _find_int(audio_node, 'Bandwidth')
    audio.sample_rate = _find_int(audio_node, 'SampleRate')
    audio.codec = _find_tag(audio_node, 'Codec')


def parse_live_channel_stat(result, body):
    root = ElementTree.fromstring(body)

    result.status = _find_tag(root, 'Status')
    if root.find('RemoteAddr') is not None:
        result.remote_addr = _find_tag(root, 'RemoteAddr')
    if root.find('ConnectedTime') is not None:
        result.connected_time = iso8601_to_unixtime(_find_tag(root, 'ConnectedTime'))

    video_node = root.find('Video')
    audio_node = root.find('Audio')

    if video_node is not None:
        result.video = LiveChannelVideoStat()
        parse_stat_video(video_node, result.video)
    if audio_node is not None:
        result.audio = LiveChannelAudioStat()
        parse_stat_audio(audio_node, result.audio)

    return result


def parse_live_channel_history(result, body):
    root = ElementTree.fromstring(body)

    records = root.findall('LiveRecord')
    for record in records:
        tmp = LiveRecord()
        tmp.start_time = iso8601_to_unixtime(_find_tag(record, 'StartTime'))
        tmp.end_time = iso8601_to_unixtime(_find_tag(record, 'EndTime'))
        tmp.remote_addr = _find_tag(record, 'RemoteAddr')
        result.records.append(tmp)

    return result


def parse_lifecycle_expiration(expiration_node):
    if expiration_node is None:
        return None

    expiration = LifecycleExpiration()

    if expiration_node.find('Days') is not None:
        expiration.days = _find_int(expiration_node, 'Days')
    elif expiration_node.find('Date') is not None:
        expiration.date = iso8601_to_date(_find_tag(expiration_node, 'Date'))
    elif expiration_node.find('CreatedBeforeDate') is not None:
        expiration.created_before_date = iso8601_to_date(_find_tag(expiration_node, 'CreatedBeforeDate'))
    elif expiration_node.find('ExpiredObjectDeleteMarker') is not None:
        expiration.expired_detete_marker = _find_bool(expiration_node, 'ExpiredObjectDeleteMarker')

    return expiration


def parse_lifecycle_abort_multipart_upload(abort_multipart_upload_node):
    if abort_multipart_upload_node is None:
        return None
    abort_multipart_upload = AbortMultipartUpload()

    if abort_multipart_upload_node.find('Days') is not None:
        abort_multipart_upload.days = _find_int(abort_multipart_upload_node, 'Days')
    elif abort_multipart_upload_node.find('CreatedBeforeDate') is not None:
        abort_multipart_upload.created_before_date = iso8601_to_date(_find_tag(abort_multipart_upload_node,
                                                                               'CreatedBeforeDate'))
    return abort_multipart_upload


def parse_lifecycle_storage_transitions(storage_transition_nodes):
    storage_transitions = []
    for storage_transition_node in storage_transition_nodes:
        storage_class = _find_tag(storage_transition_node, 'StorageClass')
        storage_transition = StorageTransition(storage_class=storage_class)
        if storage_transition_node.find('Days') is not None:
            storage_transition.days = _find_int(storage_transition_node, 'Days')
        elif storage_transition_node.find('CreatedBeforeDate') is not None:
            storage_transition.created_before_date = iso8601_to_date(_find_tag(storage_transition_node,
                                                                               'CreatedBeforeDate'))

        storage_transitions.append(storage_transition)

    return storage_transitions

def parse_lifecycle_object_taggings(lifecycle_tagging_nodes):
    
    if lifecycle_tagging_nodes is None or \
        len(lifecycle_tagging_nodes) == 0: 
        return None 
    
    tagging_rule = TaggingRule()
    for tag_node in lifecycle_tagging_nodes:
        key = _find_tag(tag_node, 'Key')
        value = _find_tag(tag_node, 'Value')
        tagging_rule.add(key, value)

    return Tagging(tagging_rule)

def parse_lifecycle_version_expiration(version_expiration_node):
    if version_expiration_node is None:
        return None

    noncurrent_days = _find_int(version_expiration_node, 'NoncurrentDays')
    expiration = NoncurrentVersionExpiration(noncurrent_days)

    return expiration

def parse_lifecycle_verison_storage_transitions(version_storage_transition_nodes):
    version_storage_transitions = []
    for transition_node in version_storage_transition_nodes:
        storage_class = _find_tag(transition_node, 'StorageClass')
        non_crurrent_days = _find_int(transition_node, 'NoncurrentDays')
        version_storage_transition = NoncurrentVersionStorageTransition(non_crurrent_days, storage_class)
        version_storage_transitions.append(version_storage_transition)

    return version_storage_transitions

def parse_get_bucket_lifecycle(result, body):

    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)

    for rule_node in root.findall('Rule'):
        expiration = parse_lifecycle_expiration(rule_node.find('Expiration'))
        abort_multipart_upload = parse_lifecycle_abort_multipart_upload(rule_node.find('AbortMultipartUpload'))
        storage_transitions = parse_lifecycle_storage_transitions(rule_node.findall('Transition'))
        tagging = parse_lifecycle_object_taggings(rule_node.findall('Tag'))
        noncurrent_version_expiration = parse_lifecycle_version_expiration(rule_node.find('NoncurrentVersionExpiration'))
        noncurrent_version_sotrage_transitions = parse_lifecycle_verison_storage_transitions(rule_node.findall('NoncurrentVersionTransition'))

        rule = LifecycleRule(
            _find_tag(rule_node, 'ID'),
            _find_tag(rule_node, 'Prefix'),
            status=_find_tag(rule_node, 'Status'),
            expiration=expiration,
            abort_multipart_upload=abort_multipart_upload,
            storage_transitions=storage_transitions,
            tagging=tagging,
            noncurrent_version_expiration = noncurrent_version_expiration,
            noncurrent_version_sotrage_transitions = noncurrent_version_sotrage_transitions
            )
        result.rules.append(rule)

    return result


def parse_get_bucket_cors(result, body):
    root = ElementTree.fromstring(body)

    for rule_node in root.findall('CORSRule'):
        rule = CorsRule()
        rule.allowed_origins = _find_all_tags(rule_node, 'AllowedOrigin')
        rule.allowed_methods = _find_all_tags(rule_node, 'AllowedMethod')
        rule.allowed_headers = _find_all_tags(rule_node, 'AllowedHeader')
        rule.expose_headers = _find_all_tags(rule_node, 'ExposeHeader')

        max_age_node = rule_node.find('MaxAgeSeconds')
        if max_age_node is not None:
            rule.max_age_seconds = int(max_age_node.text)

        result.rules.append(rule)

    return result


def to_complete_upload_request(parts):
    root = ElementTree.Element('CompleteMultipartUpload')
    for p in parts:
        part_node = ElementTree.SubElement(root, "Part")
        _add_text_child(part_node, 'PartNumber', str(p.part_number))
        _add_text_child(part_node, 'ETag', '"{0}"'.format(p.etag))

    return _node_to_string(root)


def to_batch_delete_objects_request(keys, quiet):
    root_node = ElementTree.Element('Delete')

    _add_text_child(root_node, 'Quiet', str(quiet).lower())

    for key in keys:
        object_node = ElementTree.SubElement(root_node, 'Object')
        _add_text_child(object_node, 'Key', key)

    return _node_to_string(root_node)

def to_batch_delete_objects_version_request(objectVersions, quiet):

    root_node = ElementTree.Element('Delete')

    _add_text_child(root_node, 'Quiet', str(quiet).lower())

    objectVersionList = objectVersions.object_version_list

    for ver in objectVersionList:
        object_node = ElementTree.SubElement(root_node, 'Object')
        _add_text_child(object_node, 'Key', ver.key)
        if ver.versionid != '':
            _add_text_child(object_node, 'VersionId', ver.versionid)

    return _node_to_string(root_node)


def to_put_bucket_config(bucket_config):
    root = ElementTree.Element('CreateBucketConfiguration')

    _add_text_child(root, 'StorageClass', bucket_config.storage_class)

    if bucket_config.data_redundancy_type is not None:
        _add_text_child(root, 'DataRedundancyType', bucket_config.data_redundancy_type)

    return _node_to_string(root)


def to_put_bucket_logging(bucket_logging):
    root = ElementTree.Element('BucketLoggingStatus')

    if bucket_logging.target_bucket:
        logging_node = ElementTree.SubElement(root, 'LoggingEnabled')
        _add_text_child(logging_node, 'TargetBucket', bucket_logging.target_bucket)
        _add_text_child(logging_node, 'TargetPrefix', bucket_logging.target_prefix)

    return _node_to_string(root)


def to_put_bucket_referer(bucket_referer):
    root = ElementTree.Element('RefererConfiguration')

    _add_text_child(root, 'AllowEmptyReferer', str(bucket_referer.allow_empty_referer).lower())
    list_node = ElementTree.SubElement(root, 'RefererList')

    for r in bucket_referer.referers:
        _add_text_child(list_node, 'Referer', r)

    return _node_to_string(root)


def to_put_bucket_website(bucket_website):
    root = ElementTree.Element('WebsiteConfiguration')

    index_node = ElementTree.SubElement(root, 'IndexDocument')
    _add_text_child(index_node, 'Suffix', bucket_website.index_file)

    error_node = ElementTree.SubElement(root, 'ErrorDocument')
    _add_text_child(error_node, 'Key', bucket_website.error_file)

    if len(bucket_website.rules) == 0:
        return _node_to_string(root)

    rules_node = ElementTree.SubElement(root, "RoutingRules")

    for rule in bucket_website.rules:
        rule_node = ElementTree.SubElement(rules_node, 'RoutingRule')
        _add_text_child(rule_node, 'RuleNumber', str(rule.rule_num))

        condition_node = ElementTree.SubElement(rule_node, 'Condition')
        
        if rule.condition.key_prefix_equals is not None:
            _add_text_child(condition_node, 'KeyPrefixEquals', rule.condition.key_prefix_equals)
        if rule.condition.http_err_code_return_equals is not None:    
            _add_text_child(condition_node, 'HttpErrorCodeReturnedEquals', 
                str(rule.condition.http_err_code_return_equals))
       
        for header in rule.condition.include_header_list:
            include_header_node = ElementTree.SubElement(condition_node, 'IncludeHeader')
            _add_text_child(include_header_node, 'Key', header.key)
            _add_text_child(include_header_node, 'Equals', header.equals)

        if rule.redirect is not None:    
            redirect_node = ElementTree.SubElement(rule_node, 'Redirect')

            # common
            _add_text_child(redirect_node, 'RedirectType', rule.redirect.redirect_type)
            
            if rule.redirect.pass_query_string is not None:
                _add_text_child(redirect_node, 'PassQueryString', str(rule.redirect.pass_query_string))          

            # External, AliCDN
            if rule.redirect.redirect_type in [REDIRECT_TYPE_EXTERNAL, REDIRECT_TYPE_ALICDN]:
                if rule.redirect.proto is not None:
                    _add_text_child(redirect_node, 'Protocol', rule.redirect.proto)
                if rule.redirect.host_name is not None:
                    _add_text_child(redirect_node, 'HostName', rule.redirect.host_name)
                if rule.redirect.http_redirect_code is not None:
                    _add_text_child(redirect_node, 'HttpRedirectCode', str(rule.redirect.http_redirect_code))

            # External, AliCDN, Internal
            if rule.redirect.redirect_type in [REDIRECT_TYPE_EXTERNAL, REDIRECT_TYPE_ALICDN, REDIRECT_TYPE_INTERNAL]:
                if rule.redirect.replace_key_with is not None:
                    _add_text_child(redirect_node, 'ReplaceKeyWith', rule.redirect.replace_key_with)
                if rule.redirect.replace_key_prefix_with is not None:
                    _add_text_child(redirect_node, 'ReplaceKeyPrefixWith', rule.redirect.replace_key_prefix_with)  

            # Mirror
            elif rule.redirect.redirect_type == REDIRECT_TYPE_MIRROR: 
                if rule.redirect.mirror_url is not None:
                    _add_text_child(redirect_node, 'MirrorURL', rule.redirect.mirror_url)
                if rule.redirect.mirror_url_slave is not None:
                    _add_text_child(redirect_node, 'MirrorURLSlave', rule.redirect.mirror_url_slave)
                if rule.redirect.mirror_url_probe is not None:
                    _add_text_child(redirect_node, 'MirrorURLProbe', rule.redirect.mirror_url_probe)
                if rule.redirect.mirror_pass_query_string is not None:
                    _add_text_child(redirect_node, 'MirrorPassQueryString', str(rule.redirect.mirror_pass_query_string))
                if rule.redirect.mirror_follow_redirect is not None:
                    _add_text_child(redirect_node, 'MirrorFollowRedirect', str(rule.redirect.mirror_follow_redirect))
                if rule.redirect.mirror_check_md5 is not None:
                    _add_text_child(redirect_node, 'MirrorCheckMd5', str(rule.redirect.mirror_check_md5))

                if rule.redirect.mirror_headers is not None:
                    mirror_headers_node = ElementTree.SubElement(redirect_node, 'MirrorHeaders')

                    if rule.redirect.mirror_headers.pass_all is not None:
                        _add_text_child(mirror_headers_node, 'PassAll', str(rule.redirect.mirror_headers.pass_all))

                    for pass_param in rule.redirect.mirror_headers.pass_list:
                        _add_text_child(mirror_headers_node, 'Pass', pass_param)   
                    for remove_param in rule.redirect.mirror_headers.remove_list:
                        _add_text_child(mirror_headers_node, 'Remove', remove_param)
                    for set_param in rule.redirect.mirror_headers.set_list:
                        set_node = ElementTree.SubElement(mirror_headers_node, 'Set')
                        _add_text_child(set_node, 'Key', set_param.key)
                        _add_text_child(set_node, 'Value', set_param.value)

    return _node_to_string(root)


def to_put_bucket_lifecycle(bucket_lifecycle):
    root = ElementTree.Element('LifecycleConfiguration')

    for rule in bucket_lifecycle.rules:
        rule_node = ElementTree.SubElement(root, 'Rule')
        _add_text_child(rule_node, 'ID', rule.id)
        _add_text_child(rule_node, 'Prefix', rule.prefix)
        _add_text_child(rule_node, 'Status', rule.status)

        expiration = rule.expiration
        if expiration:
            expiration_node = ElementTree.SubElement(rule_node, 'Expiration')

            if expiration.days is not None:
                _add_text_child(expiration_node, 'Days', str(expiration.days))
            elif expiration.date is not None:
                _add_text_child(expiration_node, 'Date', date_to_iso8601(expiration.date))
            elif expiration.created_before_date is not None:
                _add_text_child(expiration_node, 'CreatedBeforeDate', date_to_iso8601(expiration.created_before_date))
            elif expiration.expired_detete_marker is not None:
                _add_text_child(expiration_node, 'ExpiredObjectDeleteMarker', str(expiration.expired_detete_marker))

        abort_multipart_upload = rule.abort_multipart_upload
        if abort_multipart_upload:
            abort_multipart_upload_node = ElementTree.SubElement(rule_node, 'AbortMultipartUpload')
            if abort_multipart_upload.days is not None:
                _add_text_child(abort_multipart_upload_node, 'Days', str(abort_multipart_upload.days))
            elif abort_multipart_upload.created_before_date is not None:
                _add_text_child(abort_multipart_upload_node, 'CreatedBeforeDate',
                                date_to_iso8601(abort_multipart_upload.created_before_date))

        storage_transitions = rule.storage_transitions
        if storage_transitions:
            for storage_transition in storage_transitions:
                storage_transition_node = ElementTree.SubElement(rule_node, 'Transition')
                _add_text_child(storage_transition_node, 'StorageClass', str(storage_transition.storage_class))
                if storage_transition.days is not None:
                    _add_text_child(storage_transition_node, 'Days', str(storage_transition.days))
                elif storage_transition.created_before_date is not None:
                    _add_text_child(storage_transition_node, 'CreatedBeforeDate',
                                    date_to_iso8601(storage_transition.created_before_date))

        tagging = rule.tagging
        if tagging:
            tagging_rule = tagging.tag_set.tagging_rule
            for key in tagging.tag_set.tagging_rule:
                tag_node = ElementTree.SubElement(rule_node, 'Tag')
                _add_text_child(tag_node, 'Key', key)
                _add_text_child(tag_node, 'Value', tagging_rule[key])

        noncurrent_version_expiration = rule.noncurrent_version_expiration
        if noncurrent_version_expiration is not None:
            version_expiration_node = ElementTree.SubElement(rule_node, 'NoncurrentVersionExpiration')
            _add_text_child(version_expiration_node, 'NoncurrentDays', str(noncurrent_version_expiration.noncurrent_days))

        noncurrent_version_sotrage_transitions = rule.noncurrent_version_sotrage_transitions
        if noncurrent_version_sotrage_transitions is not None:
            for noncurrent_version_sotrage_transition in noncurrent_version_sotrage_transitions:
                version_transition_node = ElementTree.SubElement(rule_node, 'NoncurrentVersionTransition')
                _add_text_child(version_transition_node, 'NoncurrentDays', str(noncurrent_version_sotrage_transition.noncurrent_days))
                _add_text_child(version_transition_node, 'StorageClass', str(noncurrent_version_sotrage_transition.storage_class))

    return _node_to_string(root)


def to_put_bucket_cors(bucket_cors):
    root = ElementTree.Element('CORSConfiguration')

    for rule in bucket_cors.rules:
        rule_node = ElementTree.SubElement(root, 'CORSRule')
        _add_node_list(rule_node, 'AllowedOrigin', rule.allowed_origins)
        _add_node_list(rule_node, 'AllowedMethod', rule.allowed_methods)
        _add_node_list(rule_node, 'AllowedHeader', rule.allowed_headers)
        _add_node_list(rule_node, 'ExposeHeader', rule.expose_headers)

        if rule.max_age_seconds is not None:
            _add_text_child(rule_node, 'MaxAgeSeconds', str(rule.max_age_seconds))

    return _node_to_string(root)

def to_create_live_channel(live_channel):
    root = ElementTree.Element('LiveChannelConfiguration')

    _add_text_child(root, 'Description', live_channel.description)
    _add_text_child(root, 'Status', live_channel.status)
    target_node = _add_node_child(root, 'Target')

    _add_text_child(target_node, 'Type', live_channel.target.type)
    _add_text_child(target_node, 'FragDuration', str(live_channel.target.frag_duration))
    _add_text_child(target_node, 'FragCount', str(live_channel.target.frag_count))
    _add_text_child(target_node, 'PlaylistName', str(live_channel.target.playlist_name))

    return _node_to_string(root)

def to_select_object(sql, select_params):
    if (select_params is not None and 'Json_Type' in select_params):
        return to_select_json_object(sql, select_params)
    else:
        return to_select_csv_object(sql, select_params)

def to_select_csv_object(sql, select_params):
    root = ElementTree.Element('SelectRequest')
    _add_text_child(root, 'Expression', base64.b64encode(str.encode(sql)))
    input_ser = ElementTree.SubElement(root, 'InputSerialization')
    output_ser = ElementTree.SubElement(root, 'OutputSerialization')
    csv = ElementTree.SubElement(input_ser, 'CSV')
    out_csv = ElementTree.SubElement(output_ser, 'CSV')
    options = ElementTree.SubElement(root, 'Options')
   
    if (select_params is None):
        return _node_to_string(root)
    
    for key, value in select_params.items():
        if SelectParameters.CsvHeaderInfo == key:
            _add_text_child(csv, 'FileHeaderInfo', value)
        elif SelectParameters.CommentCharacter == key:
            _add_text_child(csv, SelectParameters.CommentCharacter, base64.b64encode(str.encode(value)))
        elif SelectParameters.RecordDelimiter == key:
            _add_text_child(csv, SelectParameters.RecordDelimiter, base64.b64encode(str.encode(value)))
        elif SelectParameters.OutputRecordDelimiter == key:
            _add_text_child(out_csv, SelectParameters.RecordDelimiter, base64.b64encode(str.encode(value)))
        elif SelectParameters.FieldDelimiter == key:
            _add_text_child(csv, SelectParameters.FieldDelimiter, base64.b64encode(str.encode(value)))
        elif SelectParameters.OutputFieldDelimiter == key:
            _add_text_child(out_csv, SelectParameters.FieldDelimiter, base64.b64encode(str.encode(value)))
        elif SelectParameters.QuoteCharacter == key:
            _add_text_child(csv, SelectParameters.QuoteCharacter, base64.b64encode(str.encode(value)))
        elif SelectParameters.SplitRange == key:
            _add_text_child(csv, 'Range', utils._make_split_range_string(value))
        elif SelectParameters.LineRange == key:
            _add_text_child(csv, 'Range', utils._make_line_range_string(value))
        elif SelectParameters.CompressionType == key:
            _add_text_child(input_ser, SelectParameters.CompressionType, str(value))
        elif SelectParameters.KeepAllColumns == key:
            _add_text_child(output_ser, SelectParameters.KeepAllColumns, str(value))
        elif SelectParameters.OutputRawData == key:
            _add_text_child(output_ser, SelectParameters.OutputRawData, str(value))
        elif SelectParameters.EnablePayloadCrc == key:
            _add_text_child(output_ser, SelectParameters.EnablePayloadCrc, str(value))
        elif SelectParameters.OutputHeader == key:
            _add_text_child(output_ser, SelectParameters.OutputHeader, str(value))
        elif SelectParameters.SkipPartialDataRecord == key:
            _add_text_child(options, SelectParameters.SkipPartialDataRecord, str(value))
        elif SelectParameters.MaxSkippedRecordsAllowed == key:
            _add_text_child(options, SelectParameters.MaxSkippedRecordsAllowed, str(value))
        elif SelectParameters.AllowQuotedRecordDelimiter == key:
            _add_text_child(csv, SelectParameters.AllowQuotedRecordDelimiter, str(value))
        else:
            raise SelectOperationClientError("The select_params contains unsupported key " + key, "")

    return _node_to_string(root)

def to_select_json_object(sql, select_params):
    root = ElementTree.Element('SelectRequest')
    _add_text_child(root, 'Expression', base64.b64encode(str.encode(sql)))
    input_ser = ElementTree.SubElement(root, 'InputSerialization')
    output_ser = ElementTree.SubElement(root, 'OutputSerialization')
    json = ElementTree.SubElement(input_ser, 'JSON')
    out_json = ElementTree.SubElement(output_ser, 'JSON')
    options = ElementTree.SubElement(root, 'Options')
    is_doc = select_params[SelectParameters.Json_Type] == SelectJsonTypes.DOCUMENT
    _add_text_child(json, 'Type', select_params[SelectParameters.Json_Type])

    for key, value in select_params.items(): 
        if SelectParameters.SplitRange == key and is_doc == False:
            _add_text_child(json, 'Range', utils._make_split_range_string(value))
        elif SelectParameters.LineRange == key and is_doc == False:
            _add_text_child(json, 'Range', utils._make_line_range_string(value))
        elif SelectParameters.CompressionType == key:
            _add_text_child(input_ser, SelectParameters.CompressionType, value)
        elif SelectParameters.OutputRawData == key:
            _add_text_child(output_ser, SelectParameters.OutputRawData, str(value))
        elif SelectParameters.EnablePayloadCrc == key:
            _add_text_child(output_ser, SelectParameters.EnablePayloadCrc, str(value))
        elif SelectParameters.OutputRecordDelimiter == key:
            _add_text_child(out_json, SelectParameters.RecordDelimiter, base64.b64encode(str.encode(value)))
        elif SelectParameters.SkipPartialDataRecord == key:
            _add_text_child(options, SelectParameters.SkipPartialDataRecord, str(value))
        elif SelectParameters.MaxSkippedRecordsAllowed == key:
            _add_text_child(options, SelectParameters.MaxSkippedRecordsAllowed, str(value))
        elif SelectParameters.ParseJsonNumberAsString == key:
            _add_text_child(json, SelectParameters.ParseJsonNumberAsString, str(value))
        else:
            if key != SelectParameters.Json_Type:
                raise SelectOperationClientError("The select_params contains unsupported key " + key, "")

    return _node_to_string(root)

def to_get_select_object_meta(meta_param):
    if meta_param is not None and SelectParameters.Json_Type in meta_param:
        if meta_param[SelectParameters.Json_Type] != SelectJsonTypes.LINES:
            raise SelectOperationClientError("Json_Type can only be 'LINES' for creating meta", "")
        else:
            return to_get_select_json_object_meta(meta_param)
    else:
        return to_get_select_csv_object_meta(meta_param)

def to_get_select_csv_object_meta(csv_meta_param):
    root = ElementTree.Element('CsvMetaRequest')
    input_ser = ElementTree.SubElement(root, 'InputSerialization')
    csv = ElementTree.SubElement(input_ser, 'CSV')
    if (csv_meta_param is None):
        return _node_to_string(root)
    
    for key, value in csv_meta_param.items():
        if SelectParameters.RecordDelimiter == key:
            _add_text_child(csv, SelectParameters.RecordDelimiter, base64.b64encode(str.encode(value)))
        elif SelectParameters.FieldDelimiter == key:
            _add_text_child(csv, SelectParameters.FieldDelimiter, base64.b64encode(str.encode(value)))
        elif SelectParameters.QuoteCharacter == key:
            _add_text_child(csv, SelectParameters.QuoteCharacter, base64.b64encode(str.encode(value)))
        elif SelectParameters.CompressionType == key:
            _add_text_child(input_ser, SelectParameters.CompressionType, base64.b64encode(str.encode(value)))
        elif SelectParameters.OverwriteIfExists == key:
            _add_text_child(root, SelectParameters.OverwriteIfExists, str(value))
        else:
           raise SelectOperationClientError("The csv_meta_param contains unsupported key " + key, "") 

    return _node_to_string(root)

def to_get_select_json_object_meta(json_meta_param):
    root = ElementTree.Element('JsonMetaRequest')
    input_ser = ElementTree.SubElement(root, 'InputSerialization')
    json = ElementTree.SubElement(input_ser, 'JSON')
    _add_text_child(json, 'Type', json_meta_param[SelectParameters.Json_Type]) # Json_Type是必须的
  
    for key, value in json_meta_param.items():
        if SelectParameters.OverwriteIfExists == key:
            _add_text_child(root, SelectParameters.OverwriteIfExists, str(value))
        elif SelectParameters.CompressionType == key:
             _add_text_child(input_ser, SelectParameters.CompressionType, base64.b64encode(str.encode(value)))
        else:
            if SelectParameters.Json_Type != key:
                raise SelectOperationClientError("The json_meta_param contains unsupported key " + key, "")
            
    return _node_to_string(root)

def to_put_tagging(object_tagging):
    root = ElementTree.Element("Tagging")
    tag_set = ElementTree.SubElement(root, "TagSet")

    for item in object_tagging.tag_set.tagging_rule:
        tag_xml = ElementTree.SubElement(tag_set, "Tag")
        _add_text_child(tag_xml, 'Key', item)
        _add_text_child(tag_xml, 'Value', object_tagging.tag_set.tagging_rule[item])

    return _node_to_string(root)

def parse_get_tagging(result, body):
    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)
    tagset_node = root.find('TagSet')

    if tagset_node is None:
        return result

    tagging_rules = TaggingRule()
    for tag_node in tagset_node.findall('Tag'):
        key = _find_object(tag_node, 'Key', url_encoded)
        value = _find_object(tag_node, 'Value', url_encoded)
        tagging_rules.add(key, value)
    
    result.tag_set = tagging_rules
    return result

def to_put_bucket_encryption(rule):
    root = ElementTree.Element("ServerSideEncryptionRule")
    apply_node = ElementTree.SubElement(root, "ApplyServerSideEncryptionByDefault")

    _add_text_child(apply_node, "SSEAlgorithm", rule.sse_algorithm)

    if rule.kms_master_keyid:
        _add_text_child(apply_node, "KMSMasterKeyID", rule.kms_master_keyid)

    return _node_to_string(root)

def parse_get_bucket_encryption(result, body):
    root = ElementTree.fromstring(body)
    apply_node = root.find('ApplyServerSideEncryptionByDefault')

    result.sse_algorithm = _find_tag(apply_node, "SSEAlgorithm")

    kmsnode = apply_node.find('KMSMasterKeyID')
    if kmsnode is None or kmsnode.text is None:
        result.kms_master_keyid = None 
    else:
        result.kms_master_keyid = to_string(kmsnode.text)

    return result
def parse_list_object_versions(result, body):
    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)
    result.is_truncated = _find_bool(root, 'IsTruncated')
    if result.is_truncated:
        result.next_key_marker = _find_object(root, 'NextKeyMarker', url_encoded)
        result.next_versionid_marker = _find_object(root, "NextVersionIdMarker", url_encoded)

    result.name = _find_tag(root, "Name")
    result.prefix = _find_object(root, "Prefix", url_encoded)
    result.key_marker = _find_object(root, "KeyMarker", url_encoded)
    result.versionid_marker = _find_object(root, "VersionIdMarker", url_encoded)
    result.max_keys = _find_int(root, "MaxKeys")
    result.delimiter = _find_object(root, "Delimiter", url_encoded)

    for delete_marker in root.findall("DeleteMarker"):
        deleteInfo = DeleteMarkerInfo()
        deleteInfo.key = _find_object(delete_marker, "Key", url_encoded)
        deleteInfo.versionid = _find_tag(delete_marker, "VersionId")
        deleteInfo.is_latest = _find_bool(delete_marker, "IsLatest")
        deleteInfo.last_modified = iso8601_to_unixtime(_find_tag(delete_marker, "LastModified"))
        deleteInfo.owner.id = _find_tag(delete_marker, "Owner/ID")
        deleteInfo.owner.display_name = _find_tag(delete_marker, "Owner/DisplayName")
        result.delete_marker.append(deleteInfo)

    for version in root.findall("Version"):
        versionInfo = ObjectVersionInfo()
        versionInfo.key = _find_object(version, "Key", url_encoded)
        versionInfo.versionid = _find_tag(version, "VersionId")
        versionInfo.is_latest = _find_bool(version, "IsLatest")
        versionInfo.last_modified = iso8601_to_unixtime(_find_tag(version, "LastModified"))
        versionInfo.owner.id = _find_tag(version, "Owner/ID")
        versionInfo.owner.display_name = _find_tag(version, "Owner/DisplayName")
        versionInfo.type = _find_tag(version, "Type")
        versionInfo.storage_class = _find_tag(version, "StorageClass")
        versionInfo.size = _find_int(version, "Size")
        versionInfo.etag = _find_tag(version, "ETag").strip('"')

        result.versions.append(versionInfo)

    for common_prefix in root.findall("CommonPrefixes"):
        result.common_prefix.append(_find_object(common_prefix, "Prefix", url_encoded))

    return result

def to_put_bucket_versioning(bucket_version_config):
    root = ElementTree.Element('VersioningConfiguration')

    _add_text_child(root, 'Status', str(bucket_version_config.status))

    return _node_to_string(root)

def parse_get_bucket_versioning(result, body):
    root = ElementTree.fromstring(body)

    status_node = root.find("Status")
    if status_node is None:
        result.status = None
    else:
        result.status = _find_tag(root, "Status")

    return result

def to_put_bucket_request_payment(payer):
    root = ElementTree.Element('RequestPaymentConfiguration')

    _add_text_child(root, 'Payer', payer)

    return _node_to_string(root)

def parse_get_bucket_request_payment(result, body):
    root = ElementTree.fromstring(body)

    result.payer = _find_tag(root, 'Payer')
   
    return result

def to_put_qos_info(qos_info):
    root = ElementTree.Element("QoSConfiguration")

    if qos_info.total_upload_bw is not None:
        _add_text_child(root, "TotalUploadBandwidth", str(qos_info.total_upload_bw))
    if qos_info.intranet_upload_bw is not None:
        _add_text_child(root, "IntranetUploadBandwidth", str(qos_info.intranet_upload_bw))
    if qos_info.extranet_upload_bw is not None:
        _add_text_child(root, "ExtranetUploadBandwidth", str(qos_info.extranet_upload_bw))
    if qos_info.total_download_bw is not None:
        _add_text_child(root, "TotalDownloadBandwidth", str(qos_info.total_download_bw))
    if qos_info.intranet_download_bw is not None:
        _add_text_child(root, "IntranetDownloadBandwidth", str(qos_info.intranet_download_bw))
    if qos_info.extranet_download_bw is not None:
        _add_text_child(root, "ExtranetDownloadBandwidth", str(qos_info.extranet_download_bw))
    if qos_info.total_qps is not None:
        _add_text_child(root, "TotalQps", str(qos_info.total_qps))
    if qos_info.intranet_qps is not None:
        _add_text_child(root, "IntranetQps", str(qos_info.intranet_qps))
    if qos_info.extranet_qps is not None:
        _add_text_child(root, "ExtranetQps", str(qos_info.extranet_qps))

    return _node_to_string(root)

def parse_get_qos_info(result, body):
    """解析UserQosInfo 或者BucketQosInfo

    :UserQosInfo包含成员region,其他成员同BucketQosInfo
    """
    root = ElementTree.fromstring(body)

    if hasattr(result, 'region'):
        result.region = _find_tag(root, 'Region')

    result.total_upload_bw = _find_int(root, 'TotalUploadBandwidth')
    result.intranet_upload_bw = _find_int(root, 'IntranetUploadBandwidth')
    result.extranet_upload_bw = _find_int(root, 'ExtranetUploadBandwidth')
    result.total_download_bw = _find_int(root, 'TotalDownloadBandwidth')
    result.intranet_download_bw = _find_int(root, 'IntranetDownloadBandwidth')
    result.extranet_download_bw = _find_int(root, 'ExtranetDownloadBandwidth')
    result.total_qps = _find_int(root, 'TotalQps')
    result.intranet_qps = _find_int(root, 'IntranetQps')
    result.extranet_qps = _find_int(root, 'ExtranetQps')

    return result

def parse_get_bucket_user_qos(result, body):
    root = ElementTree.fromstring(body)

    result.storage_capacity = _find_int(root, 'StorageCapacity')

    return result

def to_put_bucket_user_qos(user_qos):
    root = ElementTree.Element('BucketUserQos')

    _add_text_child(root, 'StorageCapacity', str(user_qos.storage_capacity))

    return _node_to_string(root)


def to_put_async_fetch_task(task_config):
    root = ElementTree.Element('AsyncFetchTaskConfiguration')

    _add_text_child(root, 'Url', task_config.url)
    _add_text_child(root, 'Object', task_config.object_name)

    if task_config.host is not None:    
        _add_text_child(root, 'Host', task_config.host)
    if task_config.content_md5 is not None:
        _add_text_child(root, 'ContentMD5', task_config.content_md5)
    if task_config.callback is not None:
        _add_text_child(root, 'Callback', task_config.callback)
    if task_config.ignore_same_key is not None:
        _add_text_child(root, 'IgnoreSameKey', str(task_config.ignore_same_key).lower())

    return _node_to_string(root)

def parse_put_async_fetch_task_result(result, body):
    root = ElementTree.fromstring(body)

    result.task_id = _find_tag(root, 'TaskId')

    return result

def _parse_async_fetch_task_configuration(task_info_node):
    url = _find_tag(task_info_node, 'Url')
    object_name = _find_tag(task_info_node, 'Object')
    host = _find_tag(task_info_node, 'Host')
    content_md5 = _find_tag(task_info_node, 'ContentMD5')
    callback = _find_tag(task_info_node, 'Callback')
    ignore_same_key = _find_bool(task_info_node, 'IgnoreSameKey')

    return AsyncFetchTaskConfiguration(url, object_name, host, content_md5, callback, ignore_same_key)

def parse_get_async_fetch_task_result(result, body):
    root = ElementTree.fromstring(body)

    result.task_id = _find_tag(root, 'TaskId')
    result.task_state = _find_tag(root, 'State')
    result.error_msg = _find_tag(root, 'ErrorMsg')
    result.task_config = _parse_async_fetch_task_configuration(root.find('TaskInfo'))

    return result