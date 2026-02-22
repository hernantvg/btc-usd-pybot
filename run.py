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

# --- DICCIONARIO BILINGÜE (ES / EN) ---
LANG = {
    "es": {
        "title": "BTC/USD PyBot - Terminal Cuantitativa",
        "header": "BTC/USD PyBot (V7.4 - Lógica Corregida)",
        "status_active": "SISTEMA ACTIVO 🟢",
        "status_stopped": "DETENIDO ⚪",
        "btn_start": "INICIAR",
        "btn_stop": "DETENER",
        "btn_close_all": "CERRAR TODO",
        "btn_export": "EXPORTAR LOG",
        "card_pos": "POSICIONES",
        "card_profit": "BENEFICIO GLOBAL",
        "card_spread": "SPREAD",
        "log_init": "=== BTC/USD PyBot (M15) INICIADO ===",
        "log_stop": "=== BTC/USD PyBot DETENIDO ===",
        "log_conn_ok": "✅ Conectado exitosamente a {symbol}",
        "log_err_init": "❌ Error MT5 Init: {err}",
        "log_err_login": "❌ Error Login: {err}",
        "log_err_symbol": "❌ Error: No se encuentra el símbolo {symbol}",
        "log_basket_buy": "💰 CERRANDO BASKET COMPRAS | Beneficio: ${profit:.2f}",
        "log_basket_sell": "💰 CERRANDO BASKET VENTAS | Beneficio: ${profit:.2f}",
        "log_panic": "💀 STOP LOSS GLOBAL ALCANZADO. CERRANDO TODAS LAS POSICIONES.",
        "log_stats": "📊 [M15] Precio:{p:.2f} | RSI:{rsi:.2f} | BBLow:{bblow:.2f} | BBUp:{bbup:.2f}",
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
        "title": "BTC/USD PyBot - Quant Terminal",
        "header": "BTC/USD PyBot (V7.4 - Fixed Logic)",
        "status_active": "SYSTEM ACTIVE 🟢",
        "status_stopped": "STOPPED ⚪",
        "btn_start": "START",
        "btn_stop": "STOP",
        "btn_close_all": "CLOSE ALL",
        "btn_export": "EXPORT LOG",
        "card_pos": "POSITIONS",
        "card_profit": "GLOBAL PROFIT",
        "card_spread": "SPREAD",
        "log_init": "=== BTC/USD PyBot (M15) STARTED ===",
        "log_stop": "=== BTC/USD PyBot STOPPED ===",
        "log_conn_ok": "✅ Successfully connected to {symbol}",
        "log_err_init": "❌ MT5 Init Error: {err}",
        "log_err_login": "❌ Login Error: {err}",
        "log_err_symbol": "❌ Error: Symbol {symbol} not found",
        "log_basket_buy": "💰 CLOSING BUY BASKET | Profit: ${profit:.2f}",
        "log_basket_sell": "💰 CLOSING SELL BASKET | Profit: ${profit:.2f}",
        "log_panic": "💀 GLOBAL STOP LOSS HIT. CLOSING ALL POSITIONS.",
        "log_stats": "📊 [M15] Price:{p:.2f} | RSI:{rsi:.2f} | BBLow:{bblow:.2f} | BBUp:{bbup:.2f}",
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

# --- CONFIGURACIÓN DE LA ESTRATEGIA GRID ---
SYMBOL = "BTCUSD"        
TIMEFRAME = mt5.TIMEFRAME_M15    
VOLUME = 0.01            
MAX_POSITIONS = 6        
GRID_DISTANCE_USD = 2.0 

# --- REGLAS DE DINERO (GLOBALES) ---
TARGET_PROFIT_BASKET = 5.00  
STOP_LOSS_GLOBAL = -100.00   

# --- ESTRATEGIA TÉCNICA (PERMISIVA Y CORREGIDA) ---
RSI_PERIOD = 14          
RSI_UPPER = 55           
RSI_LOWER = 45           
BB_PERIOD = 20
BB_DEV = 2.0             

MAX_SPREAD = 15000       
MAGIC_NUMBER = 777000

load_dotenv()
ACCOUNT = int(os.getenv("ACCOUNT_NUMBER", "0"))
PASSWORD = os.getenv("PASSWORD", "")
SERVER = os.getenv("SERVER", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "") 
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "") 

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("green") 

class PyBotBTC:
    def __init__(self, app, text_widget, gui_elements):
        self.app = app
        self.running = False
        self.text_widget = text_widget
        self.gui = gui_elements
        self.lang = "es" 
        self.last_log_time = 0  
        self.filling_modes = [
            ("FOK", mt5.ORDER_FILLING_FOK),
            ("IOC", mt5.ORDER_FILLING_IOC),
            ("RETURN", mt5.ORDER_FILLING_RETURN)
        ]

    def send_telegram(self, message):
        """Envía un mensaje a Telegram de forma asíncrona para no bloquear el bot"""
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return 

        def _send():
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🤖 PyBot BTC:\n{message}"}
            try:
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                self.log_raw(f"⚠️ Aviso: Falló el envío a Telegram ({e})", "info")

        threading.Thread(target=_send, daemon=True).start()

    def set_language(self, lang_code):
        self.lang = lang_code
        self.gui['lbl_header'].configure(text=self._t("header"))
        self.app.title(self._t("title"))
        self.gui['btn_start'].configure(text=self._t("btn_start"))
        self.gui['btn_stop'].configure(text=self._t("btn_stop"))
        self.gui['btn_close'].configure(text=self._t("btn_close_all"))
        self.gui['btn_export'].configure(text=self._t("btn_export"))
        self.gui['lbl_title_pos'].configure(text=self._t("card_pos"))
        self.gui['lbl_title_float'].configure(text=self._t("card_profit"))
        self.gui['lbl_title_spread'].configure(text=self._t("card_spread"))
        status_text = self._t("status_active") if self.running else self._t("status_stopped")
        self.gui['lbl_status'].configure(text=status_text)

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
        
        if send_tg:
            self.send_telegram(msg)

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
                msg = "Log exportado" if self.lang == "es" else "Log exported"
                messagebox.showinfo("OK", f"{msg}:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def connect(self):
        if not mt5.initialize():
            self.log("log_err_init", tag="error", err=mt5.last_error())
            return False
        if ACCOUNT != 0:
            if not mt5.login(ACCOUNT, password=PASSWORD, server=SERVER):
                self.log("log_err_login", tag="error", err=mt5.last_error())
                return False
        if not mt5.symbol_select(SYMBOL, True):
            self.log("log_err_symbol", tag="error", symbol=SYMBOL)
            return False
        
        self.log("log_conn_ok", tag="profit", send_tg=True, symbol=SYMBOL) 
        return True

    def get_data(self):
        rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 300)
        if rates is None or len(rates) < 300: return None
        df = pd.DataFrame(rates)
        
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1/RSI_PERIOD, min_periods=RSI_PERIOD).mean()
        loss = -delta.clip(upper=0).ewm(alpha=1/RSI_PERIOD, min_periods=RSI_PERIOD).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        sma = df['close'].rolling(window=BB_PERIOD).mean()
        std = df['close'].rolling(window=BB_PERIOD).std()
        df['BB_Up'] = sma + (std * BB_DEV)
        df['BB_Low'] = sma - (std * BB_DEV)

        return df.iloc[-1]

    def close_position(self, ticket):
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return False
        pos = positions[0]
        tick = mt5.symbol_info_tick(SYMBOL)
        if not tick: return False

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": SYMBOL,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price": tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask,
            "magic": MAGIC_NUMBER,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        for mode_name, fill_mode in self.filling_modes:
            request["type_filling"] = fill_mode
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log("log_close_ok", tag="profit", ticket=ticket, modo=mode_name)
                return True
            elif result.retcode == 10030:
                continue
            else:
                break

        self.log("log_close_err", tag="error", ticket=ticket, cmt=result.comment, code=result.retcode)
        return False

    def get_positions_summary(self):
        positions = mt5.positions_get(symbol=SYMBOL)
        if positions is None: return [], [], 0.0
        buy_positions = [p for p in positions if p.type == mt5.ORDER_TYPE_BUY and p.magic == MAGIC_NUMBER]
        sell_positions = [p for p in positions if p.type == mt5.ORDER_TYPE_SELL and p.magic == MAGIC_NUMBER]
        total_profit = sum([p.profit + p.swap for p in positions])
        return buy_positions, sell_positions, total_profit

    def manage_grid_logic(self, type_op, price):
        buy_pos, sell_pos, _ = self.get_positions_summary()
        target_list = buy_pos if type_op == mt5.ORDER_TYPE_BUY else sell_pos
        tipo_str = "BUY" if type_op == mt5.ORDER_TYPE_BUY else "SELL"
        
        if len(target_list) == 0:
            self.open_trade(type_op, price, f"Init_{tipo_str}")
            return

        if len(target_list) >= MAX_POSITIONS:
            self.log("log_grid_max", tag="error", max=MAX_POSITIONS, tipo=tipo_str)
            return 

        target_list.sort(key=lambda x: x.ticket)
        last_open_price = target_list[-1].price_open
        dist_usd = abs(price - last_open_price)

        if dist_usd >= GRID_DISTANCE_USD:
            if (type_op == mt5.ORDER_TYPE_BUY and price < last_open_price) or \
               (type_op == mt5.ORDER_TYPE_SELL and price > last_open_price):
                self.open_trade(type_op, price, f"Grid_{tipo_str}_{len(target_list)+1}")
        else:
            self.log("log_grid_wait", tag="info", dist=dist_usd, req=GRID_DISTANCE_USD)

    def open_trade(self, type_op, price, comment):
        tipo_str = "BUY" if type_op == mt5.ORDER_TYPE_BUY else "SELL"
        self.log("log_order_try", tag="info", tipo=tipo_str, precio=price, cmt=comment)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": SYMBOL,
            "volume": float(VOLUME),
            "type": type_op,
            "price": float(price),
            "magic": MAGIC_NUMBER,
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
            elif result.retcode == 10030: 
                continue 
            else:
                break 

        if result and result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log("log_order_err", tag="error", cmt=result.comment, code=result.retcode)

    def run(self):
        if not self.connect(): return
        self.gui['lbl_status'].configure(text=self._t("status_active"), text_color="#2ea043")
        self.log("log_init", tag="profit", send_tg=True) 

        while self.running:
            try:
                if not mt5.terminal_info():
                    self.connect()
                    time.sleep(5)
                    continue

                tick = mt5.symbol_info_tick(SYMBOL)
                if not tick: continue
                spread = int((tick.ask - tick.bid) / mt5.symbol_info(SYMBOL).point)
                
                buys, sells, float_profit = self.get_positions_summary()
                self.update_dashboard(len(buys) + len(sells), float_profit, spread)

                # --- GESTIÓN DE SALIDA (BASKET) ---
                profit_buy = sum([p.profit + p.swap for p in buys])
                profit_sell = sum([p.profit + p.swap for p in sells])

                if profit_buy >= TARGET_PROFIT_BASKET and buys:
                    self.log("log_basket_buy", tag="profit", send_tg=True, profit=profit_buy)
                    for p in buys: self.close_position(p.ticket)
                    time.sleep(1)

                if profit_sell >= TARGET_PROFIT_BASKET and sells:
                    self.log("log_basket_sell", tag="profit", send_tg=True, profit=profit_sell)
                    for p in sells: self.close_position(p.ticket)
                    time.sleep(1)

                if float_profit <= STOP_LOSS_GLOBAL:
                    self.log("log_panic", tag="panic", send_tg=True)
                    self.emergency_close_all()
                    self.stop()
                    break

                # --- GESTIÓN DE ENTRADA (CORREGIDA) ---
                if spread > MAX_SPREAD:
                    self.gui['lbl_spread_val'].configure(text_color="red")
                else:
                    self.gui['lbl_spread_val'].configure(text_color="#c9d1d9")
                    
                    data = self.get_data()
                    if data is not None:
                        price = data['close']
                        rsi = data['RSI']
                        bb_low = data['BB_Low']
                        bb_up = data['BB_Up']

                        # CORRECCIÓN DE LA PARADOJA: 
                        # Ahora solo evaluamos Bollinger y RSI. Ignoramos la EMA.
                        buy_cond_1 = price < (bb_low * 1.001) 
                        buy_cond_2 = rsi < RSI_LOWER
                        
                        sell_cond_1 = price > (bb_up * 0.999)
                        sell_cond_2 = rsi > RSI_UPPER

                        current_time = time.time()
                        if current_time - self.last_log_time >= 15:
                            self.log("log_stats", p=price, rsi=rsi, bblow=bb_low, bbup=bb_up)
                            self.log("log_eval_buy", c1=buy_cond_1, rsilow=RSI_LOWER, c2=buy_cond_2)
                            self.log("log_eval_sell", c1=sell_cond_1, rsiup=RSI_UPPER, c2=sell_cond_2)
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

    def update_dashboard(self, count, profit, spread):
        try:
            self.app.after(0, lambda: self.gui['lbl_pos_val'].configure(text=f"{count}/{MAX_POSITIONS}"))
            color = "#2ea043" if profit >= 0 else "#f85149"
            self.app.after(0, lambda: self.gui['lbl_float_val'].configure(text=f"${profit:.2f}", text_color=color))
            self.app.after(0, lambda: self.gui['lbl_spread_val'].configure(text=f"{spread}"))
        except: pass

    def emergency_close_all(self):
        positions = mt5.positions_get(symbol=SYMBOL)
        if positions:
            for p in positions:
                self.close_position(p.ticket)

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        if self.running:
            self.running = False
            self.gui['lbl_status'].configure(text=self._t("status_stopped"), text_color="gray")
            self.log("log_stop", tag="error", send_tg=True)


# --- GUI SETUP ---
app = ctk.CTk()
app.geometry("850x650") 

gui_elements = {}
head = ctk.CTkFrame(app, fg_color="transparent")
head.pack(fill="x", padx=20, pady=10)

gui_elements['lbl_header'] = ctk.CTkLabel(head, text="BTC/USD PyBot (V7.4)", font=("Arial", 20, "bold"))
gui_elements['lbl_header'].pack(side="left")

lang_var = ctk.StringVar(value="es")
lang_menu = ctk.CTkOptionMenu(head, values=["es", "en"], variable=lang_var, width=60)
lang_menu.pack(side="left", padx=15)

gui_elements['lbl_status'] = ctk.CTkLabel(head, text="DETENIDO", font=("Arial", 14, "bold"))
gui_elements['lbl_status'].pack(side="right")

dash = ctk.CTkFrame(app)
dash.pack(fill="x", padx=20, pady=5)

def card(parent, title_key, val):
    f = ctk.CTkFrame(parent)
    f.pack(side="left", expand=True, fill="both", padx=5, pady=5)
    lbl_title = ctk.CTkLabel(f, text=title_key, text_color="gray")
    lbl_title.pack()
    lbl_val = ctk.CTkLabel(f, text=val, font=("Arial", 22, "bold"))
    lbl_val.pack()
    return lbl_title, lbl_val

gui_elements['lbl_title_pos'], gui_elements['lbl_pos_val'] = card(dash, "POSICIONES", "0")
gui_elements['lbl_title_float'], gui_elements['lbl_float_val'] = card(dash, "BENEFICIO GLOBAL", "$0.00")
gui_elements['lbl_title_spread'], gui_elements['lbl_spread_val'] = card(dash, "SPREAD", "0")

txt_log = ctk.CTkTextbox(app, font=("Consolas", 11))
txt_log.pack(fill="both", expand=True, padx=20, pady=10)
txt_log.tag_config("trade", foreground="cyan")
txt_log.tag_config("profit", foreground="green")
txt_log.tag_config("error", foreground="red")
txt_log.tag_config("panic", background="red", foreground="white")
txt_log.tag_config("info", foreground="yellow")

bot = PyBotBTC(app, txt_log, gui_elements)

def change_lang_callback(choice):
    bot.set_language(choice)

lang_menu.configure(command=change_lang_callback)

ctrl = ctk.CTkFrame(app, fg_color="transparent")
ctrl.pack(pady=10)
gui_elements['btn_start'] = ctk.CTkButton(ctrl, text="INICIAR", command=bot.start, fg_color="green")
gui_elements['btn_start'].pack(side="left", padx=10)

gui_elements['btn_stop'] = ctk.CTkButton(ctrl, text="DETENER", command=bot.stop, fg_color="red")
gui_elements['btn_stop'].pack(side="left", padx=10)

gui_elements['btn_close'] = ctk.CTkButton(ctrl, text="CERRAR TODO", command=bot.emergency_close_all, fg_color="orange")
gui_elements['btn_close'].pack(side="left", padx=10)

gui_elements['btn_export'] = ctk.CTkButton(ctrl, text="EXPORTAR LOG", command=bot.export_log, fg_color="#3b82f6")
gui_elements['btn_export'].pack(side="left", padx=10)

bot.set_language("es")

app.mainloop()