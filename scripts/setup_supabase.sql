-- Polymarket Trading System - Supabase Schema
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Markets table
CREATE TABLE IF NOT EXISTS markets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  polymarket_id TEXT UNIQUE NOT NULL,
  question TEXT NOT NULL,
  description TEXT,
  outcome_yes TEXT DEFAULT 'Yes',
  outcome_no TEXT DEFAULT 'No',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  closed_at TIMESTAMP WITH TIME ZONE,
  resolved_at TIMESTAMP WITH TIME ZONE,
  result TEXT CHECK (result IN ('yes', 'no', 'unresolved'))
);

-- Market snapshots (historical odds)
CREATE TABLE IF NOT EXISTS market_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  yes_price DECIMAL(10,4) NOT NULL,
  no_price DECIMAL(10,4) NOT NULL,
  yes_volume DECIMAL(20,2),
  no_volume DECIMAL(20,2),
  liquidity DECIMAL(20,2)
);

-- Trades
CREATE TABLE IF NOT EXISTS trades (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  market_id UUID REFERENCES markets(id),
  user_id TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('yes', 'no')),
  amount DECIMAL(20,8) NOT NULL,
  price DECIMAL(10,4) NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'settled', 'cancelled')),
  profit_loss DECIMAL(20,8),
  placed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  settled_at TIMESTAMP WITH TIME ZONE
);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type TEXT NOT NULL CHECK (type IN ('arb_opportunity', 'price_move', 'pattern', 'volume_spike')),
  severity TEXT DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
  message TEXT NOT NULL,
  data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  acknowledged BOOLEAN DEFAULT FALSE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_snapshots_market_time ON market_snapshots(market_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type, created_at DESC);

-- Enable realtime (optional - for future use)
-- ALTER PUBLICATION supabase_realtime ADD TABLE market_snapshots;
-- ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
