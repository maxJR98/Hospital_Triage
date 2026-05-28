-- =====================================================
-- Base de datos: hospital_triage
-- Sistema Inteligente de Triage y Gestión de Fichas
-- Hospital del Norte - La Paz, El Alto
-- =====================================================
-- Versión corregida con ajustes según SRS:
--   - Campos de bloqueo de cuenta en usuarios (RF1.2)
--   - Tabla tokens_recuperacion (RF1.5)
--   - triage_sintomas vinculada a triajes (RF3.1)
--   - recepcionista_id y medico_tratante_id en fichas
--   - Tabla configuraciones para umbrales parametrizables
--   - Triggers de inmutabilidad en bitacora_auditoria (RNF2.4)
--   - Eliminación de índices redundantes
-- =====================================================

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- =====================================================
-- CREACIÓN DE LA BASE DE DATOS
-- =====================================================

CREATE DATABASE IF NOT EXISTS `hospital_triage`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `hospital_triage`;

-- =====================================================
-- TABLAS PRINCIPALES
-- =====================================================

-- ---------------------------------------------------------
-- Tabla: roles
-- Catálogo de roles del sistema (RBAC)
-- ---------------------------------------------------------
CREATE TABLE `roles` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: usuarios
-- Personal hospitalario con acceso al sistema
-- Incluye campos para bloqueo por intentos fallidos (RF1.2)
-- ---------------------------------------------------------
CREATE TABLE `usuarios` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre_completo` varchar(150) NOT NULL,
  `ci` varchar(15) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `rol_id` int(10) UNSIGNED NOT NULL,
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `intentos_fallidos` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `fecha_bloqueo` datetime DEFAULT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ci` (`ci`),
  UNIQUE KEY `uk_email` (`email`),
  KEY `fk_usuarios_rol` (`rol_id`),
  CONSTRAINT `fk_usuarios_rol` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: tokens_recuperacion
-- Tokens para restablecimiento de contraseña (RF1.5)
-- Vigencia de 30 minutos
-- ---------------------------------------------------------
CREATE TABLE `tokens_recuperacion` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `usuario_id` int(10) UNSIGNED NOT NULL,
  `token` varchar(255) NOT NULL,
  `fecha_expiracion` datetime NOT NULL,
  `usado` tinyint(1) NOT NULL DEFAULT 0,
  `fecha_creacion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_token` (`token`),
  KEY `fk_tokens_usuario` (`usuario_id`),
  CONSTRAINT `fk_tokens_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: pacientes
-- Datos personales de los pacientes
-- ---------------------------------------------------------
CREATE TABLE `pacientes` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `ci` varchar(20) NOT NULL,
  `nombre_completo` varchar(150) NOT NULL,
  `fecha_nacimiento` date NOT NULL,
  `sexo` enum('Masculino','Femenino','Otro') NOT NULL,
  `contacto` varchar(15) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ci` (`ci`),
  KEY `idx_nombre` (`nombre_completo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: fichas
-- Fichas de atención por visita del paciente
-- Incluye FK a recepcionista y médico tratante
-- ---------------------------------------------------------
CREATE TABLE `fichas` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `numero_ficha` varchar(20) NOT NULL COMMENT 'Formato: YYYY-MM-DD-NNN',
  `fecha_hora_llegada` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `paciente_id` int(10) UNSIGNED NOT NULL,
  `recepcionista_id` int(10) UNSIGNED DEFAULT NULL COMMENT 'Usuario que creó la ficha',
  `motivo_consulta` text NOT NULL,
  `estado` enum('En espera','En triage','En atención','Finalizado','Abandonó') NOT NULL DEFAULT 'En espera',
  `prioridad_final` enum('P1','P2','P3','P4','P5') DEFAULT NULL,
  `medico_triage_id` int(10) UNSIGNED DEFAULT NULL,
  `medico_tratante_id` int(10) UNSIGNED DEFAULT NULL COMMENT 'Médico que atendió al paciente',
  `diagnostico_egreso` text DEFAULT NULL,
  `hora_fin_atencion` datetime DEFAULT NULL,
  `tiempo_total_segundos` int(10) UNSIGNED DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_numero_ficha` (`numero_ficha`),
  KEY `fk_fichas_paciente` (`paciente_id`),
  KEY `fk_fichas_recepcionista` (`recepcionista_id`),
  KEY `fk_fichas_medico_triage` (`medico_triage_id`),
  KEY `fk_fichas_medico_tratante` (`medico_tratante_id`),
  KEY `idx_estado` (`estado`),
  KEY `idx_prioridad` (`prioridad_final`),
  KEY `idx_fichas_fecha_estado` (`fecha_hora_llegada`, `estado`),
  CONSTRAINT `fk_fichas_paciente` FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`),
  CONSTRAINT `fk_fichas_recepcionista` FOREIGN KEY (`recepcionista_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_fichas_medico_triage` FOREIGN KEY (`medico_triage_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_fichas_medico_tratante` FOREIGN KEY (`medico_tratante_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: historial_estados_ficha
-- Historial de cambios de estado de cada ficha (RF2.3)
-- ---------------------------------------------------------
CREATE TABLE `historial_estados_ficha` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `ficha_id` int(10) UNSIGNED NOT NULL,
  `estado_anterior` enum('En espera','En triage','En atención','Finalizado','Abandonó') NOT NULL,
  `estado_nuevo` enum('En espera','En triage','En atención','Finalizado','Abandonó') NOT NULL,
  `usuario_id` int(10) UNSIGNED NOT NULL,
  `fecha_hora` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_historial_ficha` (`ficha_id`),
  KEY `fk_historial_usuario` (`usuario_id`),
  CONSTRAINT `fk_historial_ficha` FOREIGN KEY (`ficha_id`) REFERENCES `fichas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_historial_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: triajes
-- Evaluación clínica de triage con signos vitales (RF3)
-- ---------------------------------------------------------
CREATE TABLE `triajes` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `ficha_id` int(10) UNSIGNED NOT NULL,
  `usuario_medico_id` int(10) UNSIGNED NOT NULL,
  `presion_sistolica` smallint(5) UNSIGNED DEFAULT NULL,
  `presion_diastolica` smallint(5) UNSIGNED DEFAULT NULL,
  `frecuencia_cardiaca` smallint(5) UNSIGNED DEFAULT NULL,
  `frecuencia_respiratoria` tinyint(3) UNSIGNED DEFAULT NULL,
  `temperatura` decimal(3,1) DEFAULT NULL,
  `saturacion_oxigeno` tinyint(3) UNSIGNED DEFAULT NULL,
  `nivel_dolor` tinyint(3) UNSIGNED DEFAULT NULL CHECK (`nivel_dolor` BETWEEN 0 AND 10),
  `observaciones` text DEFAULT NULL,
  `nivel_sugerido` enum('P1','P2','P3','P4','P5') NOT NULL,
  `nivel_confirmado` enum('P1','P2','P3','P4','P5') NOT NULL,
  `justificacion_modificacion` text DEFAULT NULL COMMENT 'Obligatoria si nivel_confirmado != nivel_sugerido (mín 20 chars)',
  `fecha_hora` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_triajes_ficha` (`ficha_id`),
  KEY `fk_triajes_medico` (`usuario_medico_id`),
  KEY `idx_triajes_fecha` (`fecha_hora`),
  CONSTRAINT `fk_triajes_ficha` FOREIGN KEY (`ficha_id`) REFERENCES `fichas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_triajes_medico` FOREIGN KEY (`usuario_medico_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: sintomas
-- Catálogo configurable de síntomas (RF3.1)
-- ---------------------------------------------------------
CREATE TABLE `sintomas` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: triage_sintomas (antes ficha_sintomas)
-- Relación N:M entre triajes y síntomas (RF3.1)
-- Vinculada a triajes, no a fichas
-- ---------------------------------------------------------
CREATE TABLE `triage_sintomas` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `triage_id` int(10) UNSIGNED NOT NULL,
  `sintoma_id` int(10) UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_triage_sintoma` (`triage_id`, `sintoma_id`),
  KEY `fk_ts_sintoma` (`sintoma_id`),
  CONSTRAINT `fk_ts_triage` FOREIGN KEY (`triage_id`) REFERENCES `triajes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ts_sintoma` FOREIGN KEY (`sintoma_id`) REFERENCES `sintomas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: reglas_clinicas
-- Reglas parametrizables del módulo inteligente (RF3.4)
-- ---------------------------------------------------------
CREATE TABLE `reglas_clinicas` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `parametro` enum('frecuencia_cardiaca','frecuencia_respiratoria','temperatura','saturacion_oxigeno','presion_sistolica','presion_diastolica','nivel_dolor') NOT NULL,
  `operador` enum('>','<','>=','<=','=','BETWEEN') NOT NULL,
  `valor_umbral` varchar(50) NOT NULL COMMENT 'Valor único o "min,max" para BETWEEN',
  `nivel_prioridad` enum('P1','P2','P3','P4','P5') NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `descripcion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_activo` (`activo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: configuraciones
-- Parámetros del sistema configurables (umbrales de alerta, etc.)
-- ---------------------------------------------------------
CREATE TABLE `configuraciones` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `clave` varchar(100) NOT NULL,
  `valor` varchar(255) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `fecha_modificacion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_clave` (`clave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------
-- Tabla: bitacora_auditoria
-- Registro inmutable de acciones críticas (RNF2.4)
-- ---------------------------------------------------------
CREATE TABLE `bitacora_auditoria` (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `usuario_id` int(10) UNSIGNED DEFAULT NULL,
  `accion` varchar(100) NOT NULL,
  `tabla_afectada` varchar(50) DEFAULT NULL,
  `registro_id` int(10) UNSIGNED DEFAULT NULL,
  `detalle` text DEFAULT NULL,
  `ip_origen` varchar(45) DEFAULT NULL,
  `fecha_hora` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_bitacora_usuario` (`usuario_id`),
  KEY `idx_bitacora_fecha` (`fecha_hora`),
  KEY `idx_bitacora_accion` (`accion`),
  CONSTRAINT `fk_bitacora_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TRIGGERS DE INMUTABILIDAD PARA BITÁCORA (RNF2.4)
-- =====================================================

DELIMITER //

CREATE TRIGGER `trg_bitacora_no_update`
BEFORE UPDATE ON `bitacora_auditoria`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'ERROR: La bitácora de auditoría es inmutable. No se permiten modificaciones.';
END //

CREATE TRIGGER `trg_bitacora_no_delete`
BEFORE DELETE ON `bitacora_auditoria`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'ERROR: La bitácora de auditoría es inmutable. No se permiten eliminaciones.';
END //

DELIMITER ;

-- =====================================================
-- VISTAS
-- =====================================================

-- ---------------------------------------------------------
-- Vista: vista_cola_atencion
-- Cola de pacientes en espera, ordenada por prioridad y tiempo (RF4.1)
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW `vista_cola_atencion` AS
SELECT
  `f`.`id` AS `ficha_id`,
  `f`.`numero_ficha`,
  `p`.`nombre_completo` AS `paciente_nombre`,
  `p`.`ci` AS `paciente_ci`,
  `f`.`prioridad_final`,
  `f`.`fecha_hora_llegada`,
  TIMESTAMPDIFF(MINUTE, `f`.`fecha_hora_llegada`, NOW()) AS `minutos_espera`,
  `f`.`estado`,
  `f`.`motivo_consulta`
FROM `fichas` `f`
INNER JOIN `pacientes` `p` ON `f`.`paciente_id` = `p`.`id`
WHERE `f`.`estado` IN ('En espera', 'En triage')
ORDER BY
  FIELD(`f`.`prioridad_final`, 'P1', 'P2', 'P3', 'P4', 'P5', NULL) ASC,
  `f`.`fecha_hora_llegada` ASC;

-- ---------------------------------------------------------
-- Vista: vista_resumen_diario
-- Resumen estadístico diario por prioridad (RF5.1)
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW `vista_resumen_diario` AS
SELECT
  CAST(`f`.`fecha_hora_llegada` AS DATE) AS `fecha`,
  COUNT(*) AS `total_pacientes`,
  SUM(CASE WHEN `f`.`estado` = 'Finalizado' THEN 1 ELSE 0 END) AS `atendidos`,
  SUM(CASE WHEN `f`.`estado` = 'Abandonó' THEN 1 ELSE 0 END) AS `abandonaron`,
  AVG(CASE WHEN `f`.`tiempo_total_segundos` IS NOT NULL THEN `f`.`tiempo_total_segundos` / 60 END) AS `tiempo_promedio_espera_min`,
  `f`.`prioridad_final`,
  COUNT(`f`.`prioridad_final`) AS `cantidad_por_prioridad`
FROM `fichas` `f`
GROUP BY CAST(`f`.`fecha_hora_llegada` AS DATE), `f`.`prioridad_final`;

-- =====================================================
-- DATOS SEMILLA
-- =====================================================

-- Roles del sistema
INSERT INTO `roles` (`id`, `nombre`, `descripcion`) VALUES
(1, 'Administrador', 'Gestión completa del sistema, usuarios y configuración'),
(2, 'Médico de Triage', 'Realiza la clasificación de pacientes y confirma prioridad'),
(3, 'Recepcionista', 'Registra la llegada de pacientes y crea fichas'),
(4, 'Médico Tratante', 'Atiende pacientes en consulta, actualiza estados y cierra fichas'),
(5, 'Director', 'Acceso a reportes y estadísticas únicamente');

-- Usuario administrador por defecto (contraseña: Admin2026!)
INSERT INTO `usuarios` (`id`, `nombre_completo`, `ci`, `email`, `password_hash`, `rol_id`, `estado`) VALUES
(1, 'Administrador del Sistema', '9999999', 'admin@hospitalnorte.bo', '$2b$12$LJ3m4ys2Nt0jKvGdOHmVZOQxGxMKFxZxf4Q6YH5UdYLJ3WKB3GJzO', 1, 'activo');

-- Reglas clínicas del módulo inteligente (Escala de Manchester adaptada)
INSERT INTO `reglas_clinicas` (`id`, `parametro`, `operador`, `valor_umbral`, `nivel_prioridad`, `activo`, `descripcion`) VALUES
(1, 'frecuencia_cardiaca', '>', '130', 'P2', 1, 'Taquicardia severa'),
(2, 'frecuencia_cardiaca', '<', '50', 'P3', 1, 'Bradicardia significativa'),
(3, 'saturacion_oxigeno', '<', '90', 'P1', 1, 'Hipoxemia grave'),
(4, 'saturacion_oxigeno', 'BETWEEN', '90,93', 'P2', 1, 'Hipoxemia moderada'),
(5, 'temperatura', '>', '39.5', 'P2', 1, 'Hiperpirexia'),
(6, 'temperatura', 'BETWEEN', '38.5,39.5', 'P3', 1, 'Fiebre alta'),
(7, 'presion_sistolica', '<', '90', 'P1', 1, 'Shock hipotensivo'),
(8, 'nivel_dolor', '>=', '8', 'P2', 1, 'Dolor severo'),
(9, 'frecuencia_respiratoria', '>', '30', 'P2', 1, 'Taquipnea'),
(10, 'frecuencia_respiratoria', '<', '10', 'P1', 1, 'Bradipnea crítica');

-- Catálogo de síntomas
INSERT INTO `sintomas` (`id`, `nombre`, `activo`) VALUES
(1, 'Dolor torácico', 1),
(2, 'Disnea', 1),
(3, 'Cefalea intensa', 1),
(4, 'Vómitos', 1),
(5, 'Diarrea', 1),
(6, 'Traumatismo', 1),
(7, 'Convulsiones', 1),
(8, 'Alteración de conciencia', 1),
(9, 'Hemorragia activa', 1),
(10, 'Fiebre', 1);

-- Configuraciones del sistema
INSERT INTO `configuraciones` (`clave`, `valor`, `descripcion`) VALUES
('alerta_p1_minutos', '0', 'Minutos máximos de espera para P1 (Resucitación) - atención inmediata'),
('alerta_p2_minutos', '15', 'Minutos máximos de espera para P2 (Emergencia)'),
('alerta_p3_minutos', '30', 'Minutos máximos de espera para P3 (Urgente)'),
('alerta_p4_minutos', '60', 'Minutos máximos de espera para P4 (Semi-urgente)'),
('alerta_p5_minutos', '120', 'Minutos máximos de espera para P5 (No urgente)'),
('sesion_timeout_minutos', '30', 'Tiempo de inactividad para cierre automático de sesión'),
('intentos_max_login', '5', 'Intentos fallidos antes de bloquear cuenta'),
('bloqueo_minutos', '15', 'Duración del bloqueo de cuenta en minutos'),
('token_recuperacion_minutos', '30', 'Vigencia del token de recuperación de contraseña'),
('cola_refresh_segundos', '30', 'Intervalo de actualización de la cola de atención');

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
