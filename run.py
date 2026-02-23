import logging
import threading
import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk 
from datetime import datetime
import os
import requests 
from dotenv import load_dotenv

# --- VALORES POR DEFECTO (CONFIGURABLES EN GUI) ---
DEFAULTS = {
    "SYMBOL": "BTCUSD",
    "TIMEFRAME": "D1",
    "VOLUME": 0.10,
    "MAX_POSITIONS": 5,
    "GRID_DISTANCE": 2.0,
    "ACTIVATION_PROFIT": 5.00,
    "TRAILING_STEP": 2.00,
    "STOP_LOSS": -200.00,
    "RSI_PERIOD": 14,
    "RSI_UPPER": 55,
    "RSI_LOWER": 45,
    "BB_PERIOD": 20,
    "BB_DEV": 2.0,
    "MAX_SPREAD": 2500,
    "MAGIC": 777000
}

# --- MAPEO DE TIMEFRAMES ---
TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1
}

# --- DICCIONARIO BILINGÜE (ES / EN) ---
LANG = {
    "es": {
        "title": "BTC/USD PyBot",
        "header": "PyBot Crypto BTC/USD",
        "status_active": "SISTEMA ACTIVO 🟢",
        "status_stopped": "DETENIDO ⚪",
        "btn_start": "INICIAR ESTRATEGIA",
        "btn_stop": "DETENER MOTORES",
        "btn_close_all": "PÁNICO: CERRAR TODO",
        "btn_export": "GUARDAR LOG",
        "tab_monitor": "🖥️ Monitor en Vivo",
        "tab_config": "⚙️ Configuración",
        "grp_grid": "Estrategia de Grid",
        "grp_risk": "Gestión de Riesgo & Dinero",
        "grp_tech": "Indicadores Técnicos",
        "lbl_sym": "Símbolo", "lbl_tf": "Timeframe", "lbl_vol": "Lotes", 
        "lbl_max_pos": "Max Posiciones", "lbl_grid_dist": "Distancia Grid ($)",
        "lbl_act_prof": "Trailing Start ($)", "lbl_trail_step": "Trailing Step ($)", 
        "lbl_sl": "Stop Loss Global ($)", "lbl_rsi_per": "Período RSI", 
        "lbl_rsi_up": "RSI Techo", "lbl_rsi_low": "RSI Piso",
        "lbl_bb_per": "Período Bollinger", "lbl_bb_dev": "Desviación BB",
        "lbl_spread": "Max Spread (pts)", "lbl_magic": "Magic Number",
        "log_config_load": "⚙️ Configuración cargada correctamente. Iniciando...",
        "log_config_err": "❌ Error en configuración: {err}",
        # ... (Logs anteriores mantenidos)
        "card_pos": "POSICIONES", "card_profit": "BENEFICIO GLOBAL", "card_spread": "SPREAD",
        "log_init": "=== PyBot INICIADO ===",
        "log_stop": "=== PyBot DETENIDO ===",
        "log_conn_ok": "✅ Conectado exitosamente a {symbol}",
        "log_err_init": "❌ Error MT5 Init: {err}",
        "log_err_login": "❌ Error Login: {err}",
        "log_err_symbol": "❌ Error: No se encuentra el símbolo {symbol}",
        "log_trail_act_buy": "🎯 Trailing Profit ACTIVADO en Compras | Asegurando ganancias...",
        "log_trail_act_sell": "🎯 Trailing Profit ACTIVADO en Ventas | Asegurando ganancias...",
        "log_basket_buy": "💰 CERRANDO BASKET COMPRAS (Trailing) | Beneficio final: ${profit:.2f}",
        "log_basket_sell": "💰 CERRANDO BASKET VENTAS (Trailing) | Beneficio final: ${profit:.2f}",
        "log_panic": "💀 STOP LOSS GLOBAL ALCANZADO. CERRANDO TODAS LAS POSICIONES.",
        "log_stats": "📊 [{tf}] Precio:{p:.2f} | RSI:{rsi:.2f} | BBLow:{bblow:.2f} | BBUp:{bbup:.2f}",
        "log_eval_buy": "   -> Eval Compra: Cerca BBLow({c1}) AND RSI<{rsilow}({c2})",
        "log_eval_sell": "   -> Eval Venta : Cerca BBUp({c1}) AND RSI>{rsiup}({c2})",
        "log_cond_ok": "⚡ CONDICIONES DE {tipo} CUMPLIDAS. Procesando lógica Grid...",
        "log_grid_max": "⚠️ Límite máximo de {max} posiciones alcanzado para {tipo}. Ignorando señal.",
        "log_grid_wait": "⏳ Esperando distancia Grid. Actual: ${dist:.2f} / Requerida: ${req:.2f}",
        "log_order_try": "🔄 Intentando abrir orden de {tipo} a {precio}... (Comentario: {cmt})",
        "log_fill_try": "   -> Probando modo de ejecución: {modo}",
        "log_order_ok": "🔥 ORDEN {tipo} ABIERTA | Precio: {precio} | Ticket: {ticket}",
        "log_order_err": "❌ Error abriendo orden: {cmt} (Código: {code})",
        "log_close_ok": "✅ Posición #{ticket} cerrada correctamente (Modo: {modo})",
        "log_close_err": "❌ Error cerrando #{ticket}: {cmt} (Código: {code})"
    },
    "en": {
        "title": "BTC/USD PyBot",
        "header": "PyBot Crypto BTC/USD",
        "status_active": "SYSTEM ACTIVE 🟢",
        "status_stopped": "STOPPED ⚪",
        "btn_start": "START STRATEGY",
        "btn_stop": "STOP ENGINE",
        "btn_close_all": "PANIC: CLOSE ALL",
        "btn_export": "EXPORT LOG",
        "tab_monitor": "🖥️ Live Monitor",
        "tab_config": "⚙️ Settings",
        "grp_grid": "Grid Strategy",
        "grp_risk": "Risk & Money Management",
        "grp_tech": "Technical Indicators",
        "lbl_sym": "Symbol", "lbl_tf": "Timeframe", "lbl_vol": "Lots", 
        "lbl_max_pos": "Max Positions", "lbl_grid_dist": "Grid Distance ($)",
        "lbl_act_prof": "Trailing Start ($)", "lbl_trail_step": "Trailing Step ($)", 
        "lbl_sl": "Global Stop Loss ($)", "lbl_rsi_per": "RSI Period", 
        "lbl_rsi_up": "RSI Upper", "lbl_rsi_low": "RSI Lower",
        "lbl_bb_per": "BB Period", "lbl_bb_dev": "BB Deviation",
        "lbl_spread": "Max Spread (pts)", "lbl_magic": "Magic Number",
        "log_config_load": "⚙️ Configuration loaded successfully. Starting...",
        "log_config_err": "❌ Configuration Error: {err}",
        "card_pos": "POSITIONS", "card_profit": "GLOBAL PROFIT", "card_spread": "SPREAD",
        "log_init": "=== PyBot STARTED ===",
        "log_stop": "=== PyBot STOPPED ===",
        "log_conn_ok": "✅ Successfully connected to {symbol}",
        "log_err_init": "❌ MT5 Init Error: {err}",
        "log_err_login": "❌ Login Error: {err}",
        "log_err_symbol": "❌ Error: Symbol {symbol} not found",
        "log_trail_act_buy": "🎯 Trailing Profit ACTIVATED for Buys | Locking in gains...",
        "log_trail_act_sell": "🎯 Trailing Profit ACTIVATED for Sells | Locking in gains...",
        "log_basket_buy": "💰 CLOSING BUY BASKET (Trailing) | Final Profit: ${profit:.2f}",
        "log_basket_sell": "💰 CLOSING SELL BASKET (Trailing) | Final Profit: ${profit:.2f}",
        "log_panic": "💀 GLOBAL STOP LOSS HIT. CLOSING ALL POSITIONS.",
        "log_stats": "📊 [{tf}] Price:{p:.2f} | RSI:{rsi:.2f} | BBLow:{bblow:.2f} | BBUp:{bbup:.2f}",
        "log_eval_buy": "   -> Eval Buy : Near BBLow({c1}) AND RSI<{rsilow}({c2})",
        "log_eval_sell": "   -> Eval Sell: Near BBUp({c1}) AND RSI>{rsiup}({c2})",
        "log_cond_ok": "⚡ {tipo} CONDITIONS MET. Processing Grid logic...",
        "log_grid_max": "⚠️ Max position limit of {max} reached for {tipo}. Ignoring signal.",
        "log_grid_wait": "⏳ Waiting for Grid distance. Current: ${dist:.2f} / Required: ${req:.2f}",
        "log_order_try": "🔄 Attempting to open {tipo} order at {precio}... (Comment: {cmt})",
        "log_fill_try": "   -> Testing fill mode: {modo}",
        "log_order_ok": "🔥 {tipo} ORDER OPENED | Price: {precio} | Ticket: {ticket}",
        "log_order_err": "❌ Error opening order: {cmt} (Code: {code})",
        "log_close_ok": "✅ Position #{ticket} closed successfully (Mode: {modo})",
        "log_close_err": "❌ Error closing #{ticket}: {cmt} (Code: {code})"
    }
}

load_dotenv()
ACCOUNT = int(os.getenv("ACCOUNT_NUMBER", "0"))
PASSWORD = os.getenv("PASSWORD", "")
SERVER = os.getenv("SERVER", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "") 
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "") 

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("green") 

class PyBotBTC:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.lang = "es" 
        self.last_log_time = 0
        self.filling_modes = [
            ("FOK", mt5.ORDER_FILLING_FOK),
            ("IOC", mt5.ORDER_FILLING_IOC),
            ("RETURN", mt5.ORDER_FILLING_RETURN)
        ]
        
        # Diccionario que almacenará la configuración activa al pulsar START
        self.config = {}

        # Variables Trailing
        self.max_profit_buy = 0.0
        self.trailing_buy_active = False
        self.max_profit_sell = 0.0
        self.trailing_sell_active = False

        self.setup_ui()

    def setup_ui(self):
        # --- HEADER ---
        self.head = ctk.CTkFrame(self.app, fg_color="transparent")
        self.head.pack(fill="x", padx=20, pady=10)
        self.lbl_header = ctk.CTkLabel(self.head, text=LANG[self.lang]["header"], font=("Arial", 20, "bold"))
        self.lbl_header.pack(side="left")

        self.lang_var = ctk.StringVar(value="es")
        self.lang_menu = ctk.CTkOptionMenu(self.head, values=["es", "en"], variable=self.lang_var, width=60, command=self.change_lang)
        self.lang_menu.pack(side="left", padx=15)

        self.lbl_status = ctk.CTkLabel(self.head, text=LANG[self.lang]["status_stopped"], font=("Arial", 14, "bold"), text_color="gray")
        self.lbl_status.pack(side="right")

        # --- TABS ---
        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=5)
        self.tab_mon = self.tabview.add(LANG[self.lang]["tab_monitor"])
        self.tab_conf = self.tabview.add(LANG[self.lang]["tab_config"])

        # === TAB 1: MONITOR ===
        self.dash = ctk.CTkFrame(self.tab_mon)
        self.dash.pack(fill="x", pady=5)
        
        self.lbl_title_pos, self.lbl_pos_val = self.create_card(self.dash, "card_pos", "0/0")
        self.lbl_title_float, self.lbl_float_val = self.create_card(self.dash, "card_profit", "$0.00")
        self.lbl_title_spread, self.lbl_spread_val = self.create_card(self.dash, "card_spread", "0")

        self.text_widget = ctk.CTkTextbox(self.tab_mon, font=("Consolas", 11))
        self.text_widget.pack(fill="both", expand=True, pady=10)
        self.configure_log_tags()

        # === TAB 2: CONFIGURATION ===
        self.entries = {}
        self.create_config_form()

        # --- CONTROLS ---
        ctrl = ctk.CTkFrame(self.app, fg_color="transparent")
        ctrl.pack(pady=10, fill="x", padx=20)
        
        self.btn_start = ctk.CTkButton(ctrl, text=LANG[self.lang]["btn_start"], command=self.start, fg_color="green", height=40)
        self.btn_start.pack(side="left", expand=True, fill="x", padx=5)
        
        self.btn_stop = ctk.CTkButton(ctrl, text=LANG[self.lang]["btn_stop"], command=self.stop, fg_color="red", height=40)
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=5)
        
        self.btn_close = ctk.CTkButton(ctrl, text=LANG[self.lang]["btn_close_all"], command=self.emergency_close_all, fg_color="orange", height=40)
        self.btn_close.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_export = ctk.CTkButton(ctrl, text=LANG[self.lang]["btn_export"], command=self.export_log, fg_color="#3b82f6", height=40)
        self.btn_export.pack(side="left", expand=True, fill="x", padx=5)

    def create_card(self, parent, title_key, val):
        f = ctk.CTkFrame(parent)
        f.pack(side="left", expand=True, fill="both", padx=5, pady=5)
        lbl_title = ctk.CTkLabel(f, text=LANG[self.lang][title_key], text_color="gray")
        lbl_title.pack()
        lbl_val = ctk.CTkLabel(f, text=val, font=("Arial", 22, "bold"))
        lbl_val.pack()
        return lbl_title, lbl_val

    def create_config_form(self):
        # Grid System (Column 0)
        f_grid = ctk.CTkFrame(self.tab_conf)
        f_grid.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(f_grid, text=LANG[self.lang]["grp_grid"], font=("Arial", 12, "bold"), text_color="#2ea043").grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=5)
        
        self.add_entry(f_grid, "lbl_sym", "SYMBOL", DEFAULTS["SYMBOL"], 1, 0)
        self.add_entry(f_grid, "lbl_vol", "VOLUME", DEFAULTS["VOLUME"], 1, 2)
        
        # Timeframe Combo
        ctk.CTkLabel(f_grid, text=LANG[self.lang]["lbl_tf"]).grid(row=2, column=0, padx=10, pady=2, sticky="e")
        self.combo_tf = ctk.CTkOptionMenu(f_grid, values=list(TIMEFRAME_MAP.keys()))
        self.combo_tf.set(DEFAULTS["TIMEFRAME"])
        self.combo_tf.grid(row=2, column=1, padx=10, pady=2, sticky="ew")

        self.add_entry(f_grid, "lbl_max_pos", "MAX_POSITIONS", DEFAULTS["MAX_POSITIONS"], 2, 2)
        self.add_entry(f_grid, "lbl_grid_dist", "GRID_DISTANCE", DEFAULTS["GRID_DISTANCE"], 3, 0)
        self.add_entry(f_grid, "lbl_magic", "MAGIC", DEFAULTS["MAGIC"], 3, 2)

        # Money Rules (Column 0)
        f_money = ctk.CTkFrame(self.tab_conf)
        f_money.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(f_money, text=LANG[self.lang]["grp_risk"], font=("Arial", 12, "bold"), text_color="#db6d28").grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=5)
        
        self.add_entry(f_money, "lbl_act_prof", "ACTIVATION_PROFIT", DEFAULTS["ACTIVATION_PROFIT"], 1, 0)
        self.add_entry(f_money, "lbl_trail_step", "TRAILING_STEP", DEFAULTS["TRAILING_STEP"], 1, 2)
        self.add_entry(f_money, "lbl_sl", "STOP_LOSS", DEFAULTS["STOP_LOSS"], 2, 0)
        self.add_entry(f_money, "lbl_spread", "MAX_SPREAD", DEFAULTS["MAX_SPREAD"], 2, 2)

        # Technical (Column 0)
        f_tech = ctk.CTkFrame(self.tab_conf)
        f_tech.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(f_tech, text=LANG[self.lang]["grp_tech"], font=("Arial", 12, "bold"), text_color="#3b82f6").grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=5)
        
        self.add_entry(f_tech, "lbl_rsi_per", "RSI_PERIOD", DEFAULTS["RSI_PERIOD"], 1, 0)
        self.add_entry(f_tech, "lbl_rsi_up", "RSI_UPPER", DEFAULTS["RSI_UPPER"], 1, 2)
        self.add_entry(f_tech, "lbl_rsi_low", "RSI_LOWER", DEFAULTS["RSI_LOWER"], 2, 0)
        self.add_entry(f_tech, "lbl_bb_per", "BB_PERIOD", DEFAULTS["BB_PERIOD"], 2, 2)
        self.add_entry(f_tech, "lbl_bb_dev", "BB_DEV", DEFAULTS["BB_DEV"], 3, 0)

    def add_entry(self, parent, label_key, config_key, default_val, r, c):
        lbl = ctk.CTkLabel(parent, text=LANG[self.lang][label_key])
        lbl.grid(row=r, column=c, padx=10, pady=2, sticky="e")
        entry = ctk.CTkEntry(parent, placeholder_text=str(default_val))
        entry.insert(0, str(default_val))
        entry.grid(row=r, column=c+1, padx=10, pady=2, sticky="ew")
        self.entries[config_key] = entry # Store reference
        # Store label ref to update language later if needed (skipped for brevity)

    def get_config_from_gui(self):
        try:
            cfg = {}
            cfg["SYMBOL"] = self.entries["SYMBOL"].get().upper()
            cfg["VOLUME"] = float(self.entries["VOLUME"].get())
            cfg["MAX_POSITIONS"] = int(self.entries["MAX_POSITIONS"].get())
            cfg["GRID_DISTANCE"] = float(self.entries["GRID_DISTANCE"].get())
            cfg["MAGIC"] = int(self.entries["MAGIC"].get())
            
            cfg["ACTIVATION_PROFIT"] = float(self.entries["ACTIVATION_PROFIT"].get())
            cfg["TRAILING_STEP"] = float(self.entries["TRAILING_STEP"].get())
            cfg["STOP_LOSS"] = float(self.entries["STOP_LOSS"].get())
            cfg["MAX_SPREAD"] = int(self.entries["MAX_SPREAD"].get())
            
            cfg["RSI_PERIOD"] = int(self.entries["RSI_PERIOD"].get())
            cfg["RSI_UPPER"] = int(self.entries["RSI_UPPER"].get())
            cfg["RSI_LOWER"] = int(self.entries["RSI_LOWER"].get())
            cfg["BB_PERIOD"] = int(self.entries["BB_PERIOD"].get())
            cfg["BB_DEV"] = float(self.entries["BB_DEV"].get())
            
            tf_str = self.combo_tf.get()
            cfg["TIMEFRAME"] = TIMEFRAME_MAP.get(tf_str, mt5.TIMEFRAME_M15)
            cfg["TIMEFRAME_STR"] = tf_str
            
            return cfg
        except ValueError as e:
            self.log("log_config_err", tag="error", err=str(e))
            return None

    def configure_log_tags(self):
        self.text_widget.tag_config("trade", foreground="cyan")
        self.text_widget.tag_config("profit", foreground="green")
        self.text_widget.tag_config("error", foreground="red")
        self.text_widget.tag_config("panic", background="red", foreground="white")
        self.text_widget.tag_config("info", foreground="yellow")

    def change_lang(self, lang_code):
        self.lang = lang_code
        self.lbl_header.configure(text=LANG[self.lang]["header"])
        self.app.title(LANG[self.lang]["title"])
        self.btn_start.configure(text=LANG[self.lang]["btn_start"])
        self.btn_stop.configure(text=LANG[self.lang]["btn_stop"])
        self.btn_close.configure(text=LANG[self.lang]["btn_close_all"])
        self.btn_export.configure(text=LANG[self.lang]["btn_export"])
        
        self.tabview._segmented_button._buttons_dict[self.tab_mon].configure(text=LANG[self.lang]["tab_monitor"])
        self.tabview._segmented_button._buttons_dict[self.tab_conf].configure(text=LANG[self.lang]["tab_config"])
        
        self.lbl_title_pos.configure(text=LANG[self.lang]["card_pos"])
        self.lbl_title_float.configure(text=LANG[self.lang]["card_profit"])
        self.lbl_title_spread.configure(text=LANG[self.lang]["card_spread"])

    def _t(self, key, **kwargs):
        text = LANG[self.lang].get(key, key)
        return text.format(**kwargs) if kwargs else text

    def log(self, msg_key, tag=None, send_tg=False, **kwargs):
        msg = self._t(msg_key, **kwargs)
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {msg}"
        print(formatted_msg)
        def _write():
            try:
                self.text_widget.configure(state='normal')
                self.text_widget.insert(tk.END, formatted_msg + '\n', tag)
                self.text_widget.configure(state='disabled')
                self.text_widget.see(tk.END)
            except: pass
        self.app.after(0, _write)
        if send_tg: self.send_telegram(msg)

    def log_raw(self, msg, tag=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {msg}"
        def _write():
            try:
                self.text_widget.configure(state='normal')
                self.text_widget.insert(tk.END, formatted_msg + '\n', tag)
                self.text_widget.configure(state='disabled')
                self.text_widget.see(tk.END)
            except: pass
        self.app.after(0, _write)

    def send_telegram(self, message):
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return 
        def _send():
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🤖 PyBot:\n{message}"}
            try: requests.post(url, json=payload, timeout=5)
            except Exception as e: pass
        threading.Thread(target=_send, daemon=True).start()

    def connect(self):
        if not mt5.initialize():
            self.log("log_err_init", tag="error", err=mt5.last_error())
            return False
        if ACCOUNT != 0:
            if not mt5.login(ACCOUNT, password=PASSWORD, server=SERVER):
                self.log("log_err_login", tag="error", err=mt5.last_error())
                return False
        symbol = self.config["SYMBOL"]
        if not mt5.symbol_select(symbol, True):
            self.log("log_err_symbol", tag="error", symbol=symbol)
            return False
        self.log("log_conn_ok", tag="profit", send_tg=True, symbol=symbol) 
        return True

    def get_data(self):
        symbol = self.config["SYMBOL"]
        tf = self.config["TIMEFRAME"]
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, 300)
        if rates is None or len(rates) < 300: return None
        df = pd.DataFrame(rates)
        
        rsi_p = self.config["RSI_PERIOD"]
        bb_p = self.config["BB_PERIOD"]
        bb_dev = self.config["BB_DEV"]

        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1/rsi_p, min_periods=rsi_p).mean()
        loss = -delta.clip(upper=0).ewm(alpha=1/rsi_p, min_periods=rsi_p).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        sma = df['close'].rolling(window=bb_p).mean()
        std = df['close'].rolling(window=bb_p).std()
        df['BB_Up'] = sma + (std * bb_dev)
        df['BB_Low'] = sma - (std * bb_dev)
        return df.iloc[-1]

    def close_position(self, ticket):
        symbol = self.config["SYMBOL"]
        magic = self.config["MAGIC"]
        positions = mt5.positions_get(ticket=ticket)
        if not positions: return False
        pos = positions[0]
        tick = mt5.symbol_info_tick(symbol)
        if not tick: return False

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price": tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask,
            "magic": magic,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        for mode_name, fill_mode in self.filling_modes:
            request["type_filling"] = fill_mode
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log("log_close_ok", tag="profit", ticket=ticket, modo=mode_name)
                return True
            elif result.retcode == 10030: continue
            else: break
        self.log("log_close_err", tag="error", ticket=ticket, cmt=result.comment, code=result.retcode)
        return False

    def get_positions_summary(self):
        symbol = self.config["SYMBOL"]
        magic = self.config["MAGIC"]
        positions = mt5.positions_get(symbol=symbol)
        if positions is None: return [], [], 0.0
        buy_positions = [p for p in positions if p.type == mt5.ORDER_TYPE_BUY and p.magic == magic]
        sell_positions = [p for p in positions if p.type == mt5.ORDER_TYPE_SELL and p.magic == magic]
        total_profit = sum([p.profit + p.swap for p in positions])
        return buy_positions, sell_positions, total_profit

    def manage_grid_logic(self, type_op, price):
        buy_pos, sell_pos, _ = self.get_positions_summary()
        target_list = buy_pos if type_op == mt5.ORDER_TYPE_BUY else sell_pos
        tipo_str = "BUY" if type_op == mt5.ORDER_TYPE_BUY else "SELL"
        
        max_pos = self.config["MAX_POSITIONS"]
        grid_dist = self.config["GRID_DISTANCE"]

        if len(target_list) == 0:
            self.open_trade(type_op, price, f"Init_{tipo_str}")
            return

        if len(target_list) >= max_pos:
            self.log("log_grid_max", tag="error", max=max_pos, tipo=tipo_str)
            return 

        target_list.sort(key=lambda x: x.ticket)
        last_open_price = target_list[-1].price_open
        dist_usd = abs(price - last_open_price)

        if dist_usd >= grid_dist:
            if (type_op == mt5.ORDER_TYPE_BUY and price < last_open_price) or \
               (type_op == mt5.ORDER_TYPE_SELL and price > last_open_price):
                self.open_trade(type_op, price, f"Grid_{tipo_str}_{len(target_list)+1}")
        else:
            self.log("log_grid_wait", tag="info", dist=dist_usd, req=grid_dist)

    def open_trade(self, type_op, price, comment):
        symbol = self.config["SYMBOL"]
        magic = self.config["MAGIC"]
        vol = self.config["VOLUME"]
        
        tipo_str = "BUY" if type_op == mt5.ORDER_TYPE_BUY else "SELL"
        self.log("log_order_try", tag="info", tipo=tipo_str, precio=price, cmt=comment)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(vol),
            "type": type_op,
            "price": float(price),
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        
        result = None
        for mode_name, fill_mode in self.filling_modes:
            self.log("log_fill_try", tag="info", modo=mode_name)
            request["type_filling"] = fill_mode
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log("log_order_ok", tag="trade", send_tg=True, tipo=tipo_str, precio=price, ticket=result.order)
                return 
            elif result.retcode == 10030: continue 
            else: break 

        if result and result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log("log_order_err", tag="error", cmt=result.comment, code=result.retcode)

    def run(self):
        # 1. Intentar conectar y cargar config
        if not self.connect(): 
            self.running = False
            self.lbl_status.configure(text=LANG[self.lang]["status_stopped"], text_color="gray")
            return

        symbol = self.config["SYMBOL"]
        max_pos = self.config["MAX_POSITIONS"]
        act_prof = self.config["ACTIVATION_PROFIT"]
        trail_step = self.config["TRAILING_STEP"]
        sl_global = self.config["STOP_LOSS"]
        max_spread = self.config["MAX_SPREAD"]
        
        rsi_low = self.config["RSI_LOWER"]
        rsi_up = self.config["RSI_UPPER"]

        self.lbl_status.configure(text=LANG[self.lang]["status_active"], text_color="#2ea043")
        self.log("log_init", tag="profit", send_tg=True) 

        while self.running:
            try:
                if not mt5.terminal_info():
                    self.connect()
                    time.sleep(5)
                    continue

                tick = mt5.symbol_info_tick(symbol)
                if not tick: continue
                spread = int((tick.ask - tick.bid) / mt5.symbol_info(symbol).point)
                
                buys, sells, float_profit = self.get_positions_summary()
                self.update_dashboard(len(buys) + len(sells), float_profit, spread, max_pos)

                # --- GESTIÓN DE SALIDA (TRAILING PROFIT) ---
                profit_buy = sum([p.profit + p.swap for p in buys])
                profit_sell = sum([p.profit + p.swap for p in sells])

                if not buys:
                    self.trailing_buy_active = False
                    self.max_profit_buy = 0.0
                if not sells:
                    self.trailing_sell_active = False
                    self.max_profit_sell = 0.0

                # Lógica Trailing COMPRAS
                if buys:
                    if profit_buy >= act_prof:
                        if not self.trailing_buy_active:
                            self.trailing_buy_active = True
                            self.max_profit_buy = profit_buy
                            self.log("log_trail_act_buy", tag="info", send_tg=True)
                        if profit_buy > self.max_profit_buy:
                            self.max_profit_buy = profit_buy 

                    if self.trailing_buy_active:
                        if profit_buy <= (self.max_profit_buy - trail_step):
                            self.log("log_basket_buy", tag="profit", send_tg=True, profit=profit_buy)
                            for p in buys: self.close_position(p.ticket)
                            self.trailing_buy_active = False
                            self.max_profit_buy = 0.0
                            time.sleep(1)

                # Lógica Trailing VENTAS
                if sells:
                    if profit_sell >= act_prof:
                        if not self.trailing_sell_active:
                            self.trailing_sell_active = True
                            self.max_profit_sell = profit_sell
                            self.log("log_trail_act_sell", tag="info", send_tg=True)
                        if profit_sell > self.max_profit_sell:
                            self.max_profit_sell = profit_sell 

                    if self.trailing_sell_active:
                        if profit_sell <= (self.max_profit_sell - trail_step):
                            self.log("log_basket_sell", tag="profit", send_tg=True, profit=profit_sell)
                            for p in sells: self.close_position(p.ticket)
                            self.trailing_sell_active = False
                            self.max_profit_sell = 0.0
                            time.sleep(1)

                # Pánico Global
                if float_profit <= sl_global:
                    self.log("log_panic", tag="panic", send_tg=True)
                    self.emergency_close_all()
                    self.stop()
                    break

                # --- GESTIÓN DE ENTRADA ---
                if spread > max_spread:
                    self.lbl_spread_val.configure(text_color="red")
                else:
                    self.lbl_spread_val.configure(text_color="#c9d1d9")
                    
                    data = self.get_data()
                    if data is not None:
                        price = data['close']
                        rsi = data['RSI']
                        bb_low = data['BB_Low']
                        bb_up = data['BB_Up']

                        buy_cond_1 = price < (bb_low * 1.001) 
                        buy_cond_2 = rsi < rsi_low
                        
                        sell_cond_1 = price > (bb_up * 0.999)
                        sell_cond_2 = rsi > rsi_up

                        current_time = time.time()
                        if current_time - self.last_log_time >= 15:
                            self.log("log_stats", tf=self.config["TIMEFRAME_STR"], p=price, rsi=rsi, bblow=bb_low, bbup=bb_up)
                            self.log("log_eval_buy", c1=buy_cond_1, rsilow=rsi_low, c2=buy_cond_2)
                            self.log("log_eval_sell", c1=sell_cond_1, rsiup=rsi_up, c2=sell_cond_2)
                            self.last_log_time = current_time

                        if buy_cond_1 and buy_cond_2:
                            self.log("log_cond_ok", tag="trade", tipo="BUY")
                            self.manage_grid_logic(mt5.ORDER_TYPE_BUY, tick.ask)
                            time.sleep(1) 
                        
                        elif sell_cond_1 and sell_cond_2:
                            self.log("log_cond_ok", tag="trade", tipo="SELL")
                            self.manage_grid_logic(mt5.ORDER_TYPE_SELL, tick.bid)
                            time.sleep(1)

                time.sleep(1) 

            except Exception as e:
                self.log_raw(f"❌ Exception in main loop: {e}", "error")
                time.sleep(2)

    def update_dashboard(self, count, profit, spread, max_pos):
        try:
            self.app.after(0, lambda: self.lbl_pos_val.configure(text=f"{count}/{max_pos}"))
            color = "#2ea043" if profit >= 0 else "#f85149"
            self.app.after(0, lambda: self.lbl_float_val.configure(text=f"${profit:.2f}", text_color=color))
            self.app.after(0, lambda: self.lbl_spread_val.configure(text=f"{spread}"))
        except: pass

    def emergency_close_all(self):
        # Para cerrar todo, necesitamos saber el simbolo activo, o cerrar todo lo de la cuenta
        # Intentaremos usar la config si existe, sino, intentamos leer de la GUI o hardcode
        symbol = self.config.get("SYMBOL", self.entries["SYMBOL"].get().upper())
        if not mt5.initialize(): mt5.initialize()
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            for p in positions:
                self.close_position(p.ticket)

    def start(self):
        if not self.running:
            # Leer Configuración de la GUI
            cfg = self.get_config_from_gui()
            if not cfg: return # Error en validación
            
            self.config = cfg # Guardar config para el hilo
            self.log("log_config_load", tag="info")
            self.tabview.set(LANG[self.lang]["tab_monitor"]) # Cambiar a tab monitor

            self.running = True
            threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        if self.running:
            self.running = False
            self.lbl_status.configure(text=LANG[self.lang]["status_stopped"], text_color="gray")
            self.log("log_stop", tag="error", send_tg=True)
    
    def export_log(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Log"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    log_content = self.text_widget.get("1.0", tk.END)
                    file.write(log_content)
                messagebox.showinfo("OK", "Log Exported")
            except Exception as e:
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry("900x750") 
    bot = PyBotBTC(app)
    app.mainloop()