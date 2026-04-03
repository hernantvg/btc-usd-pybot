import MetaTrader5 as mt5
import time
import telebot
import os
import threading
from dotenv import load_dotenv

# Cargar credenciales desde tu .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)

# --- CONFIGURACIÓN DE TUS RUTAS ESPECÍFICAS ---
ACCOUNTS = {
    "Elev8_Terminal": {
        "path": r"C:\Program Files\Elev8 MT5 Terminal\terminal64.exe",
    },
    "MT5_Standard": {
        "path": r"C:\Program Files\MetaTrader 5\terminal64.exe",
    }
}

class MultiTerminalMonitor:
    def __init__(self):
        self.history = {name: {} for name in ACCOUNTS} # Historial de tickets por cuenta
        self.running = True

    def log_to_telegram(self, message):
        try:
            bot.send_message(CHAT_ID, message, parse_mode="Markdown")
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")

    def process_account(self, name, path):
        """Alterna el foco a la instancia específica y procesa datos"""
        # Cambiamos el foco del SDK a esta ruta específica
        if not mt5.initialize(path=path):
            print(f"⚠️ No se pudo conectar con {name}. Error: {mt5.last_error()}")
            return

        acc = mt5.account_info()
        if not acc:
            mt5.shutdown()
            return

        # 1. Monitoreo de Riesgo (Drawdown > 50%)
        drawdown = ((acc.balance - acc.equity) / acc.balance) * 100 if acc.balance > 0 else 0
        if drawdown > 50:
            self.log_to_telegram(f"💀 *ALERTA CRÍTICA: {name}*\nDrawdown: `{drawdown:.2f}%`\nEquity: `{acc.equity:.2f}`")

        # 2. Monitoreo de Operaciones
        positions = mt5.positions_get()
        current_tickets = {p.ticket: p for p in positions} if positions else {}

        # Detectar Nuevas Aperturas
        for ticket, p in current_tickets.items():
            if ticket not in self.history[name]:
                tipo = "🟢 BUY" if p.type == 0 else "🔴 SELL"
                msg = (f"📥 *[{name}] NUEVA OPERACIÓN*\n"
                       f"Símbolo: `{p.symbol}`\n"
                       f"Tipo: {tipo}\n"
                       f"Lote: `{p.volume}`")
                self.log_to_telegram(msg)

        # Detectar Cierres
        closed_tickets = set(self.history[name].keys()) - set(current_tickets.keys())
        for ticket in closed_tickets:
            # Consultar historial antes de perder el foco
            deals = mt5.history_deals_get(ticket=ticket)
            profit = sum(d.profit for d in deals) if deals else 0
            emoji = "💰" if profit >= 0 else "💸"
            self.log_to_telegram(f"🏁 *[{name}] OPERACIÓN CERRADA*\nID: `{ticket}`\n{emoji} Profit: `{profit:.2f}`")

        # Actualizar historial local de esta cuenta
        self.history[name] = current_tickets
        
        # IMPORTANTE: shutdown para liberar el recurso y poder cambiar de instancia en el siguiente ciclo
        mt5.shutdown()

    def run(self):
        self.log_to_telegram("🛡️ *Guardian Multi-MT5 Iniciado*\nMonitoreando Elev8 y Standard.")
        while self.running:
            for name, config in ACCOUNTS.items():
                try:
                    self.process_account(name, config["path"])
                except Exception as e:
                    print(f"Error procesando {name}: {e}")
            time.sleep(5) # Pausa entre escaneos completos

monitor = MultiTerminalMonitor()

# --- COMANDOS INTERACTIVOS ---
@bot.message_handler(commands=['status'])
def status_command(message):
    summary = "📋 *ESTADO GLOBAL DE CUENTAS*\n\n"
    for name, config in ACCOUNTS.items():
        if mt5.initialize(path=config["path"]):
            acc = mt5.account_info()
            if acc:
                summary += (f"🔹 *{name}*\n"
                            f"Balance: `{acc.balance:.2f}`\n"
                            f"Equity: `{acc.equity:.2f}`\n"
                            f"Trades: `{len(mt5.positions_get())}`\n\n")
            mt5.shutdown()
    bot.reply_to(message, summary, parse_mode="Markdown")

if __name__ == "__main__":
    # Hilo para el loop de escaneo
    t = threading.Thread(target=monitor.run)
    t.daemon = True
    t.start()

    print("Bot activo. Presiona Ctrl+C para salir.")
    bot.infinity_polling()