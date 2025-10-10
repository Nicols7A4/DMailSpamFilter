CREATE DATABASE IF NOT EXISTS ia_t2_filtrospam
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ia_t2_filtrospAM; -- cuidado: usa el nombre exacto (ia_t2_filtrospam)

-- USERS (sin hash de contraseña por ahora)
CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_plain VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- MESSAGES
CREATE TABLE IF NOT EXISTS messages (
  id INT PRIMARY KEY AUTO_INCREMENT,
  sender_id INT NOT NULL,
  recipient_id INT NOT NULL,
  subject VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_spam BOOLEAN DEFAULT 0,
  spam_score DOUBLE DEFAULT 0,
  explanation TEXT NULL,
  status ENUM('unread','read') DEFAULT 'unread',
  INDEX idx_recipient_spam (recipient_id, is_spam, created_at),
  CONSTRAINT fk_msg_sender FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_msg_recipient FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- WHITELIST (opcional, para “remitente conocido”)
CREATE TABLE IF NOT EXISTS whitelist (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  trusted_email VARCHAR(255) NOT NULL,
  UNIQUE KEY uniq_user_trusted (user_id, trusted_email),
  CONSTRAINT fk_whitelist_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
