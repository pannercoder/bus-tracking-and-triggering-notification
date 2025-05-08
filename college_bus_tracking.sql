-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 23, 2025 at 09:57 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.0.28

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `college_bus_tracking`
--

-- --------------------------------------------------------

--
-- Table structure for table `bus_info`
--

CREATE TABLE `bus_info` (
  `bus_no` varchar(20) NOT NULL,
  `route_no` int(11) NOT NULL,
  `route_name` varchar(50) NOT NULL,
  `latitude` decimal(10,6) NOT NULL,
  `longitude` decimal(10,6) NOT NULL,
  `avg_speed` decimal(5,2) DEFAULT NULL,
  `departure` varchar(255) NOT NULL,
  `arrival` varchar(255) NOT NULL,
  `via` text DEFAULT NULL,
  `departure_time` time NOT NULL,
  `next_stop` varchar(255) DEFAULT NULL,
  `eta` time NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bus_info`
--

INSERT INTO `bus_info` (`bus_no`, `route_no`, `route_name`, `latitude`, `longitude`, `avg_speed`, `departure`, `arrival`, `via`, `departure_time`, `next_stop`, `eta`) VALUES
('', 2, '', 0.000000, 0.000000, NULL, '', '', NULL, '00:00:00', NULL, '00:00:00'),
('TN-72-AN-2538', 1, 'velachery to thruvanmaiyur', 12.981359, 80.242034, 43.64, 'velachery', 'thiruvanmaiyur', 'velachery,tansi nagar, baby nagar, bharathi nagar, pilaiyar kovil, tharamani, srp tools, tidel park, jeyanthi theater, thruvanmaiyur', '12:23:56', '', '00:00:00');

-- --------------------------------------------------------

--
-- Table structure for table `bus_stops`
--

CREATE TABLE `bus_stops` (
  `place` varchar(255) NOT NULL,
  `latitude` decimal(10,8) NOT NULL,
  `longitude` decimal(11,8) NOT NULL,
  `district` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bus_stops`
--

INSERT INTO `bus_stops` (`place`, `latitude`, `longitude`, `district`) VALUES
('tenkasi new bus stand', 8.97137300, 77.30163700, 'tenkasi'),
('tenkasi old bus stand', 8.97137300, 77.30163700, 'tenkasi'),
('melameignanapuram bus stand', 8.93387200, 77.34467900, 'tenaksi'),
('keela puliyur bus stand', 8.95746580, 77.31733530, 'tenkasi'),
('pavoorchatram bus stand', 8.91941080, 77.37842910, 'tenkasi'),
('mspv polytechnic collge', 8.91737300, 77.37761500, 'tenkasi'),
('mahzilvanadhapuram bus tand', 8.95746580, 77.31733530, 'tenkasi'),
('salaipudhur', 8.89188100, 77.42238100, 'Tenkasi'),
('Adaikalapattinam Bus Stand', 8.88734900, 77.43073500, 'Tenkasi'),
('Athiyuthu', 8.87939800, 77.45483100, 'Tenkasi'),
('Alangulam', 8.86684800, 77.49553700, 'Tenkasi'),
('Maranthai', 8.81822000, 77.56402400, 'Tirunelveli'),
('pudhur', 8.80848100, 77.57826500, 'tirunelveli'),
('Seethaparpanallur', 8.78862600, 77.60594100, 'Tirunelveli'),
('Einsten College', 8.78349500, 77.61337400, 'Tirunelveli'),
('Rani anna college bus stop', 8.74578300, 77.66045200, 'Tirunelveli'),
('Tirunelveli Railway Station Bus Stand', 8.73052000, 77.71013300, 'Tirunelveli'),
('Tirunelveli New Bus Stand', 8.70124300, 77.72579800, 'Tirunelveli'),
('Home', 8.51471900, 77.86232000, 'Tuticoorin'),
('Karungadal', 8.50021900, 77.87249400, 'tuticoorin'),
('Nochikulam', 8.49213500, 77.88012100, 'tuticoorin'),
('Chetikulam bus Stand', 8.48446700, 77.89682100, 'tuticoorin'),
('panamparai bus stand', 8.46909000, 77.92307700, 'tuticoorin'),
('Sathankulam bus stand', 8.44743700, 77.91445800, 'Tuticoorin'),
('Thisayanvilai bus stop', 8.33606600, 77.86517500, 'Tirunelveli'),
('velachery', 12.97618800, 80.22149900, 'chennai'),
('tansi nagar', 12.97863000, 80.22541700, 'chennai'),
('baby nagar', 12.98183200, 80.23067100, 'chennai'),
('bharathi nagar', 12.98131600, 80.23432200, 'chennai'),
('pilaiyar kovil', 12.98138300, 80.23818500, 'chennai'),
('tharamani', 12.98129700, 80.24138000, 'chennai'),
('srp tools', 12.98031900, 80.25170000, 'chennai'),
('tidel park', 12.98797800, 80.25211600, 'chennai'),
('thiruvanmaiyur', 12.98746500, 80.25930500, 'chennai');

-- --------------------------------------------------------

--
-- Table structure for table `user_data`
--

CREATE TABLE `user_data` (
  `Username` varchar(255) DEFAULT NULL,
  `bus_number` int(11) DEFAULT NULL,
  `stop_location` varchar(255) DEFAULT NULL,
  `user_lat` varchar(255) DEFAULT NULL,
  `user_lng` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `id` int(11) DEFAULT NULL,
  `phone_number` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_data`
--

INSERT INTO `user_data` (`Username`, `bus_number`, `stop_location`, `user_lat`, `user_lng`, `email`, `password`, `id`, `phone_number`) VALUES
('Sam Charles', 1, 'tharamani', '12.981451', '80.2429047', 'samcharles290@gmail.com', 'masleschar3002', 1, '9003777487');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bus_info`
--
ALTER TABLE `bus_info`
  ADD PRIMARY KEY (`bus_no`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
