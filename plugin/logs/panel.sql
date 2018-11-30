-- phpMyAdmin SQL Dump
-- version 4.4.15.10
-- https://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2018-02-03 12:05:38
-- 服务器版本： 5.5.57
-- PHP Version: 5.4.45

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `panel_logs`
--
CREATE DATABASE IF NOT EXISTS `panel_logs` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `panel_logs`;

-- --------------------------------------------------------

--
-- 表的结构 `errorlog`
--

CREATE TABLE IF NOT EXISTS `errorlog` (
  `id` int(11) NOT NULL,
  `site` varchar(64) NOT NULL,
  `logtime` int(11) DEFAULT NULL,
  `errorid` varchar(24) DEFAULT NULL,
  `level` varchar(24) DEFAULT NULL,
  `errorinfo` varchar(512) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `ip_days`
--

CREATE TABLE IF NOT EXISTS `ip_days` (
  `id` int(11) NOT NULL,
  `site` varchar(64) NOT NULL,
  `ip` varchar(16) NOT NULL,
  `num` bigint(16) NOT NULL,
  `start_time` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `logs`
--

CREATE TABLE IF NOT EXISTS `logs` (
  `id` int(11) NOT NULL,
  `site` varchar(64) NOT NULL,
  `total_size` bigint(16) DEFAULT NULL,
  `access_num` bigint(16) DEFAULT NULL,
  `post_num` bigint(16) DEFAULT NULL,
  `get_num` bigint(20) DEFAULT NULL,
  `expiredtime` int(11) DEFAULT NULL,
  `lasttime` int(11) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `normallog`
--

CREATE TABLE IF NOT EXISTS `normallog` (
  `id` int(11) NOT NULL,
  `site` varchar(64) DEFAULT NULL COMMENT '域名',
  `size` int(11) DEFAULT NULL COMMENT '流量大小',
  `logtime` int(11) DEFAULT NULL COMMENT '请求时间',
  `url` varchar(512) DEFAULT NULL COMMENT '请求地址',
  `ip` varchar(15) DEFAULT NULL,
  `terminal` varchar(30) DEFAULT NULL COMMENT '终端',
  `status` smallint(3) DEFAULT NULL COMMENT '状态码',
  `referer` varchar(512) DEFAULT NULL COMMENT '来路',
  `headers` varchar(512) DEFAULT NULL COMMENT '请求头部',
  `mode` varchar(8) DEFAULT NULL COMMENT '请求方式',
  `spider` varchar(24) DEFAULT NULL COMMENT '蜘蛛',
  `browser` varchar(64) DEFAULT NULL COMMENT '浏览器',
  `agreement` varchar(12) DEFAULT NULL COMMENT '请求协议'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `referer_days`
--

CREATE TABLE IF NOT EXISTS `referer_days` (
  `id` int(11) NOT NULL,
  `site` varchar(64) NOT NULL,
  `referer` varchar(512) NOT NULL,
  `num` bigint(16) NOT NULL,
  `start_time` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `times_traffic`
--

CREATE TABLE IF NOT EXISTS `times_traffic` (
  `id` int(11) NOT NULL,
  `site` varchar(64) NOT NULL COMMENT '域名',
  `start_time` int(11) DEFAULT NULL COMMENT '起始时间',
  `access_num` bigint(16) DEFAULT NULL COMMENT '请求数目',
  `s502` int(11) DEFAULT NULL COMMENT '502的数目',
  `s500` int(11) DEFAULT NULL COMMENT '500的数目',
  `s200` bigint(20) DEFAULT NULL,
  `s404` int(11) DEFAULT NULL,
  `s403` int(11) DEFAULT NULL,
  `Windows` bigint(20) DEFAULT NULL,
  `Android` int(11) DEFAULT NULL,
  `iPhone` int(11) DEFAULT NULL,
  `iPad` int(11) DEFAULT NULL,
  `Mac_OS` int(11) DEFAULT NULL,
  `linux` int(11) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `url_days`
--

CREATE TABLE IF NOT EXISTS `url_days` (
  `id` int(11) NOT NULL,
  `site` varchar(64) NOT NULL,
  `url` varchar(512) NOT NULL,
  `start_time` int(11) NOT NULL,
  `num` bigint(16) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `errorlog`
--
ALTER TABLE `errorlog`
  ADD PRIMARY KEY (`id`),
  ADD KEY `site` (`site`),
  ADD KEY `errorid` (`errorid`),
  ADD KEY `level` (`level`),
  ADD KEY `errorinfo` (`errorinfo`(255)),
  ADD KEY `logtime` (`logtime`) USING BTREE;

--
-- Indexes for table `ip_days`
--
ALTER TABLE `ip_days`
  ADD PRIMARY KEY (`id`),
  ADD KEY `site` (`site`),
  ADD KEY `ip` (`ip`),
  ADD KEY `start_time` (`start_time`),
  ADD KEY `num` (`num`) USING BTREE;

--
-- Indexes for table `logs`
--
ALTER TABLE `logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `site` (`site`),
  ADD KEY `total_size` (`total_size`),
  ADD KEY `access_num` (`access_num`),
  ADD KEY `post_num` (`post_num`),
  ADD KEY `get_num` (`get_num`),
  ADD KEY `expiredtime` (`expiredtime`),
  ADD KEY `lasttime` (`lasttime`);

--
-- Indexes for table `normallog`
--
ALTER TABLE `normallog`
  ADD PRIMARY KEY (`id`),
  ADD KEY `site` (`site`),
  ADD KEY `size` (`size`),
  ADD KEY `url` (`url`(255)),
  ADD KEY `ip` (`ip`),
  ADD KEY `terminal` (`terminal`),
  ADD KEY `status` (`status`),
  ADD KEY `referer` (`referer`(255)),
  ADD KEY `headers` (`headers`(255)),
  ADD KEY `mode` (`mode`),
  ADD KEY `spider` (`spider`),
  ADD KEY `browser` (`browser`),
  ADD KEY `agreement` (`agreement`),
  ADD KEY `logtime` (`logtime`) USING BTREE;

--
-- Indexes for table `referer_days`
--
ALTER TABLE `referer_days`
  ADD PRIMARY KEY (`id`),
  ADD KEY `site` (`site`),
  ADD KEY `referer` (`referer`(333)),
  ADD KEY `start_time` (`start_time`),
  ADD KEY `num` (`num`) USING BTREE;

--
-- Indexes for table `times_traffic`
--
ALTER TABLE `times_traffic`
  ADD PRIMARY KEY (`id`),
  ADD KEY `site` (`site`),
  ADD KEY `access_num` (`access_num`),
  ADD KEY `s502` (`s502`),
  ADD KEY `s500` (`s500`),
  ADD KEY `start_time` (`start_time`) USING BTREE,
  ADD KEY `s200` (`s200`),
  ADD KEY `s404` (`s404`),
  ADD KEY `s403` (`s403`),
  ADD KEY `Windows` (`Windows`),
  ADD KEY `Android` (`Android`),
  ADD KEY `iPhone` (`iPhone`),
  ADD KEY `iPad` (`iPad`),
  ADD KEY `Mac_OS` (`Mac_OS`),
  ADD KEY `linux` (`linux`);

--
-- Indexes for table `url_days`
--
ALTER TABLE `url_days`
  ADD PRIMARY KEY (`id`),
  ADD KEY `site` (`site`),
  ADD KEY `start_time` (`start_time`) USING BTREE,
  ADD KEY `url` (`url`(333)),
  ADD KEY `num` (`num`) USING BTREE;

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `errorlog`
--
ALTER TABLE `errorlog`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `ip_days`
--
ALTER TABLE `ip_days`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `logs`
--
ALTER TABLE `logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `normallog`
--
ALTER TABLE `normallog`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `referer_days`
--
ALTER TABLE `referer_days`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `times_traffic`
--
ALTER TABLE `times_traffic`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `url_days`
--
ALTER TABLE `url_days`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
