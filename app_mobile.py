import streamlit as st
import re

st.set_page_config(page_title="Risk Manager AI - Mobile", page_icon="📱", layout="centered")

st.markdown("<h2 style='text-align: center;'>📱 RISK MANAGER AI</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Copia, Pega y Calcula tu Lotaje al Instante</p>", unsafe_allow_html=True)

# --- FUNCIÓN DE LECTURA E INTERPRETACIÓN (PARSER) ---
def parsear_texto_senal(texto):
    texto_upper = texto.upper()
    
    # 1. Detectar Activo
    patron_activo = r'\b(EURUSD|GBPUSD|USDJPY|USDCAD|AUDUSD|XAUUSD|GOLD|ORO|US30|USTEC|NAS100|BTCUSD|ETHUSD)\b'
    match_activo = re.search(patron_activo, texto_upper)
    activo_detectado = match_activo.group(1) if match_activo else "XAUUSD"
    
    # 2. Buscar números en el texto
    numeros = re.findall(r'\b\d+(?:\.\d+)?\b', texto)
    
    precio_ent = None
    stop_l = None
    take_p = None
    
    # Buscar patrones específicos si contienen SL / TP
    match_sl = re.search(r'(?:SL|STOP LOSS|STOP)[\s:-]*(\d+(?:\.\d+)?)', texto_upper)
    match_tp = re.search(r'(?:TP|TAKE PROFIT|TARGET)[\s:-]*(\d+(?:\.\d+)?)', texto_upper)
    match_ep = re.search(r'(?:EP|ENTRY|ENTRADA|PRECIO|AT)[\s:-]*(\d+(?:\.\d+)?)', texto_upper)
    
    if match_sl:
        stop_l = float(match_sl.group(1))
    if match_tp:
        take_p = float(match_tp.group(1))
    if match_ep:
        precio_ent = float(match_ep.group(1))
        
    # Si no se usaron palabras clave como SL/TP, tomar los números en orden secuencial
    if not stop_l and len(numeros) >= 2:
        precio_ent = float(numeros[0])
        stop_l = float(numeros[1])
        if len(numeros) >= 3:
            take_p = float(numeros[2])
            
    return activo_detectado, precio_ent, stop_l, take_p

# --- FUNCIONES MATEMÁTICAS ---
def calcular_distancia(p_entrada, p_stop, sym):
    dist = abs(p_entrada - p_stop)
    sym_u = sym.upper()
    if "JPY" in sym_u:
        return round(dist * 100, 1), "pips"
    elif "XAU" in sym_u or "GOLD" in sym_u or "ORO" in sym_u or "US30" in sym_u or "USTEC" in sym_u or "NAS" in sym_u:
        return round(dist, 2), "pts"
    else:
        return round(dist * 10000, 1), "pips"

def calcular_lotaje(riesgo_usd, p_entrada, p_stop, sym):
    dist = abs(p_entrada - p_stop)
    if dist == 0:
        return 0.01
    sym_u = sym.upper()
    
    if "XAU" in sym_u or "GOLD" in sym_u or "ORO" in sym_u:
        contract_size = 100
    elif "US30" in sym_u or "USTEC" in sym_u or "NAS" in sym_u:
        contract_size = 1.0
    else:
        contract_size = 100000
    
    loss_per_lot = dist * contract_size
    if loss_per_lot <= 0:
        return 0.01
    lotes = riesgo_usd / loss_per_lot
    return max(0.01, round(lotes, 2))


# --- INTERFAZ USUARIO ---
st.subheader("📋 Pegar Mensaje de Señal")
texto_copiado = st.text_area("Pega aquí el texto completo de Telegram / WhatsApp:", height=100, placeholder="Ejemplo: BUY XAUUSD EP 4343.10 SL 4329.00 TP 4380")

# Valores por defecto en sesión
if "f_activo" not in st.session_state: st.session_state.f_activo = "XAUUSD"
if "f_entrada" not in st.session_state: st.session_state.f_entrada = 4343.10
if "f_sl" not in st.session_state: st.session_state.f_sl = 4329.00

if st.button("⚡ PROCESAR Y EXTRAER DATOS", use_container_width=True):
    if texto_copiado.strip():
        act, ent, sl, tp = parsear_texto_senal(texto_copiado)
        if act: st.session_state.f_activo = act
        if ent: st.session_state.f_entrada = ent
        if sl: st.session_state.f_sl = sl
        st.success("¡Datos extraídos con éxito!")
    else:
        st.warning("Por favor pega algún texto primero.")

st.divider()

# Parámetros de Cuenta
col_c1, col_c2 = st.columns(2)
with col_c1:
    balance = st.number_input("Balance ($)", value=100000.0, step=1000.0)
with col_c2:
    riesgo_pct = st.number_input("Riesgo (%)", value=0.30, step=0.05)

# Datos Confirmados
simbolo = st.text_input("Activo", value=st.session_state.f_activo)
col_d1, col_d2 = st.columns(2)
with col_d1:
    precio_entrada = st.number_input("Precio Entrada", value=float(st.session_state.f_entrada), format="%.5f")
with col_d2:
    stop_loss = st.number_input("Stop Loss", value=float(st.session_state.f_sl), format="%.5f")

# Botón Principal
if st.button("🧮 CALCULAR LOTE EXACTO", type="primary", use_container_width=True):
    if precio_entrada == stop_loss:
        st.error("El Stop Loss no puede ser igual al Precio de Entrada.")
    else:
        riesgo_usd = balance * (riesgo_pct / 100.0)
        dist_val, unidad = calcular_distancia(precio_entrada, stop_loss, simbolo)
        lotes = calcular_lotaje(riesgo_usd, precio_entrada, stop_loss, simbolo)
        
        es_compra = stop_loss < precio_entrada
        direccion = "🟢 COMPRA (BUY)" if es_compra else "🔴 VENTA (SELL)"
        
        st.markdown(f"### Operación: {direccion}")
        st.success(f"**Riesgo Máximo:** ${riesgo_usd:,.2f} USD ({riesgo_pct}%)")
        st.info(f"**Distancia SL:** {dist_val} {unidad}")
        st.warning(f"**📦 Lote a Usar:** `{lotes:.2f}` lotes")