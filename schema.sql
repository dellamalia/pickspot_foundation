-- ============================================================
--  PICKSPOT DATABASE SCHEMA
--  Engine: MySQL 8.0+ | Charset: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS pickspot_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pickspot_db;

-- ------------------------------------------------------------
-- TABLE: users
-- ------------------------------------------------------------
CREATE TABLE users (
    id_user      INT           NOT NULL AUTO_INCREMENT,
    nama         VARCHAR(100)  NOT NULL,
    email        VARCHAR(150)  NOT NULL UNIQUE,
    password     VARCHAR(255)  NOT NULL,          -- SHA-256 hex
    role         ENUM('admin','staff','member') NOT NULL DEFAULT 'member',
    created_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_user)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- TABLE: spots  (pengganti tabel Produk)
-- ------------------------------------------------------------
CREATE TABLE spots (
    id_spot         INT             NOT NULL AUTO_INCREMENT,
    nama_spot       VARCHAR(150)    NOT NULL,
    deskripsi       TEXT,
    lokasi          VARCHAR(200)    NOT NULL,
    harga_estimasi  DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    stok_booking    INT             NOT NULL DEFAULT 10,
    gambar_url      VARCHAR(255)    DEFAULT NULL,
    rating          DECIMAL(2,1)    NOT NULL DEFAULT 4.5,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_spot)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- TABLE: bookings  (pengganti tabel Transaksi)
-- ------------------------------------------------------------
CREATE TABLE bookings (
    id_booking    INT      NOT NULL AUTO_INCREMENT,
    id_user       INT      NOT NULL,
    id_spot       INT      NOT NULL,
    tanggal_waktu DATETIME NOT NULL,
    status        ENUM('pending','confirmed','cancelled') NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_booking),
    CONSTRAINT fk_booking_user FOREIGN KEY (id_user)
        REFERENCES users(id_user) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_booking_spot FOREIGN KEY (id_spot)
        REFERENCES spots(id_spot) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- SEED DATA
-- ------------------------------------------------------------
-- Default accounts (password: admin123 | staff123)
INSERT INTO users (nama, email, password, role) VALUES
('Admin PickSpot',  'admin@pickspot.id', SHA2('admin123', 256), 'admin'),
('Staff Bandung',   'staff@pickspot.id', SHA2('staff123', 256), 'staff');

-- Sample spots (mirroring pitch deck venues)
INSERT INTO spots (nama_spot, deskripsi, lokasi, harga_estimasi, stok_booking, rating) VALUES
('Atmosphere Resort Café',    'Café premium dengan view pegunungan dan ambiance cozy di Bandung Utara.', 'Kota Bandung', 75000, 15, 4.6),
('Paris Van Java',            'Mal modern dengan beragam pilihan kuliner dan café instagrammable.',       'Kota Bandung', 50000, 20, 4.6),
('23 Paskal',                 'Shopping center trendi dengan food court dan café untuk hangout seru.',   'Kota Bandung', 45000, 18, 4.6),
('ArtSociates Art Gallery',   'Galeri seni kontemporer dengan café estetis dan seating area nyaman.',    'Kota Bandung', 60000, 12, 4.5),
('KinoKimi Backyard',         'Spot outdoor cozy dengan konsep taman dan menu minuman kekinian.',        'Kota Bandung', 40000, 10, 4.4),
('Taman Hutan Raya',          'Destinasi alam segar, cocok untuk piknik dan hangout santai.',            'Kota Bandung', 20000, 25, 4.7),
('Free and Music Café',       'Café dengan nuansa musik live dan menu kopi spesialti.',                  'Jatinangor',   35000,  8, 4.3),
('MyBoo.kit Café',            'Café berkonsep buku dan tanaman indoor, estetik banget!',                 'Jatinangor',   30000, 14, 4.5);
