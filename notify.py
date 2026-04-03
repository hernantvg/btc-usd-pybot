import MetaTrader5 as mt5
import time
import requests

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8514838077:AAEM0SVDOwt0gbfQz_CRLRor1nRAIEthse0"
CHAT_ID = "-1003776198675"
SYMBOL_MONITOR = ""  # Vacío para monitorear todos los símbolos
CHECK_INTERVAL = 5   # Segundos entre cada revisión

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def monitor_mt5():
    if not mt5.initialize():
        print("Error al iniciar MT5")
        return

    print("Bot de monitoreo iniciado...")
    send_telegram("🚀 *Bot de Monitoreo MT5 Activo*")

    last_positions = set()
    
    while True:
        # 1. Obtener información de la cuenta
        account_info = mt5.account_info()
        if account_info is None:
            time.sleep(CHECK_INTERVAL)
            continue

        balance = account_info.balance
        equity = account_info.equity
        
        # 2. Lógica de Drawdown (Alerta 50%)
        drawdown_percent = ((balance - equity) / balance) * 100
        if drawdown_percent > 50:
            send_telegram(f"⚠️ *ALERTA DE RIESGO*\nDrawdown crítico: {drawdown_percent:.2f}%\nEquity: {equity:.2f}")

        # 3. Monitoreo de Operaciones (Apertura y Cierre)
        current_positions = mt5.positions_get()
        current_ids = {p.ticket for p in current_positions}

        # Detectar Nuevas Operaciones
        for p in current_positions:
            if p.ticket not in last_positions:
                msg = (f"🔵 *Operación Abierta*\n"
                       f"Ticket: {p.ticket}\n"
                       f"Símbolo: {p.symbol}\n"
                       f"Tipo: {'Buy' if p.type == 0 else 'Sell'}\n"
                       f"Volumen: {p.volume}")
                send_telegram(msg)

        # Detectar Operaciones Cerradas
        closed_ids = last_positions - current_ids
        for ticket in closed_ids:
            # Buscamos en el historial para ver el resultado
            history = mt5.history_deals_get(ticket=ticket)
            pnl = "N/A"
            if history:
                pnl = sum(deal.profit for deal in history)
            
            send_telegram(f"🔴 *Operación Cerrada*\nTicket: {ticket}\nBeneficio: {pnl}")

        last_positions = current_ids
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_mt5()