import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
import json

API_URL = "http://127.0.0.1:8000"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen3:4b-instruct")


# --- FITUR BERLANGGANAN (SUBSCRIPTION) ---
def check_subscription():
    try:
        res = requests.get(f"{API_URL}/subscription/status")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        pass
    return {"plan_name": "Free", "is_active": True}

def upgrade_subscription(plan, days):
    try:
        res = requests.post(f"{API_URL}/subscription/subscribe", json={
            "plan_name": plan,
            "duration_days": days
        })
        return res.json()
    except Exception as e:
        return {"status": "error", "message": "Gagal terhubung ke server backend"}

sub_info = check_subscription()

# Let's add sidebar subscription status indicator
st.sidebar.subheader(f"💳 Paket: {sub_info.get('plan_name', 'Free')}")
if sub_info.get('plan_name') == 'Free':
    st.sidebar.warning("Anda menggunakan Paket Gratis")
else:
    st.sidebar.success("Paket Premium Aktif! ✨")

st.set_page_config(page_title="Warehouse AI | Dashboard", page_icon="📦", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#182b3a; --muted:#728292; --line:#e6edf0; }
.stApp { background:linear-gradient(180deg,#f2f7f6 0,#f7f9fb 360px,#f7f9fb 100%); color:var(--ink); }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1360px; padding-top:1.5rem; padding-bottom:4rem; }
h1,h2,h3,h4 { font-family:'Manrope',sans-serif !important; color:var(--ink); letter-spacing:-.025em; }
h2 { margin-top:1.8rem !important; margin-bottom:.25rem !important; }
h4 { font-size:1rem !important; }
p, label, [data-testid="stCaptionContainer"] { color:#657786; }
.hero { padding:1.75rem 2rem; margin-bottom:1.4rem; border-radius:22px; color:white; background:linear-gradient(115deg,#123b46,#087e75 62%,#22a18c); box-shadow:0 16px 36px #155e5a22; }
.hero h1 { color:white; font-size:2.1rem; margin:0 0 .45rem; }
.hero p { color:#d5eeea; margin:0; font-size:1rem; }
[data-testid="stMetric"] { background:white; border:1px solid var(--line); border-radius:16px; padding:1rem 1.1rem; box-shadow:0 4px 14px #203d4a08; }
[data-testid="stMetricLabel"] { color:var(--muted); }
[data-testid="stMetricValue"] { color:var(--ink); font-family:'Manrope',sans-serif; }
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] { background:white; border:1px solid var(--line); border-radius:16px; padding:.35rem; }
div[data-testid="stExpander"] { background:white; border:1px solid var(--line); border-radius:14px; }
.plan-card { min-height:190px; padding:1.25rem; background:white; border:1px solid var(--line); border-radius:18px; box-shadow:0 6px 20px #203d4a08; }
.plan-card.featured { border:2px solid #168b7e; box-shadow:0 10px 24px #168b7e20; }
.plan-name { color:#526574; font-size:.8rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em; }
.plan-price { color:#182b3a; font:800 1.8rem Manrope,sans-serif; margin:.35rem 0; }
.plan-detail { color:#728292; font-size:.9rem; line-height:1.7; }
[data-testid="stForm"] { border:1px solid var(--line); border-radius:16px; background:white; padding:1rem; }
</style>
<div class="hero"><h1>📦 Warehouse Control Center</h1><p>Semua stok dan aktivitas gudang Anda, terlihat jelas dalam satu dashboard.</p></div>
""", unsafe_allow_html=True)

def api_get(path):
    response = requests.get(f"{API_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()

def api_post(path, payload):
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

try:
    summary = api_get("/dashboard")
    items = api_get("/items")
except requests.RequestException:
    st.error("Backend FastAPI belum berjalan. Jalankan backend terlebih dahulu.")
    st.code("uvicorn backend.main:app --reload")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Produk", summary["total_products"])
col2.metric("Total Unit Stok", summary["total_units"])
col3.metric("Low Stock", summary["low_stock"])
col4.metric("Out of Stock", summary["out_of_stock"])

PLANS = {
    "Free": {"price": 0, "limit": 10, "description": "Cocok untuk mulai menata stok."},
    "Basic": {"price": 25000, "limit": 25, "description": "Lebih banyak ruang untuk usaha berkembang."},
    "Premium": {"price": 50000, "limit": None, "description": "Kelola barang tanpa batas."},
}
if "subscription_plan" not in st.session_state:
    st.session_state.subscription_plan = "Free"

st.subheader("Paket langganan")
st.caption("Pilih kapasitas yang sesuai dengan kebutuhan gudang Anda. Harga per bulan; pilihan paket saat ini masih berupa simulasi lokal.")
plan_columns = st.columns(3, gap="medium")
for column, (plan_name, plan) in zip(plan_columns, PLANS.items()):
    with column:
        featured = " featured" if plan_name == "Basic" else ""
        price_label = "Gratis" if plan["price"] == 0 else f"Rp{plan['price']:,}".replace(",", ".")
        item_limit = "Barang tak terbatas" if plan["limit"] is None else f"Maksimal {plan['limit']} barang"
        st.markdown(
            f'<div class="plan-card{featured}"><div class="plan-name">{plan_name}</div>'
            f'<div class="plan-price">{price_label}<span style="font-size:.85rem;font-weight:500;color:#728292">'
            f'{"" if plan["price"] == 0 else " / bulan"}</span></div>'
            f'<div class="plan-detail">{item_limit}<br>{plan["description"]}</div></div>',
            unsafe_allow_html=True,
        )
        button_label = "Paket aktif" if st.session_state.subscription_plan == plan_name else f"Pilih {plan_name}"
        if st.button(button_label, key=f"choose_{plan_name}", use_container_width=True,
                     disabled=st.session_state.subscription_plan == plan_name):
            if plan_name == "Free":
                upgrade_subscription("Free", 30)
                st.session_state.subscription_plan = "Free"
                st.success("Berhasil beralih ke Paket Gratis!")
                st.rerun()
            else:
                st.session_state.selected_checkout_plan = plan_name
                st.session_state.show_payment_modal = True
                st.rerun()


# --- PROSES PEMBAYARAN LANGGANAN ---
if "show_payment_modal" not in st.session_state:
    st.session_state.show_payment_modal = False
if "selected_checkout_plan" not in st.session_state:
    st.session_state.selected_checkout_plan = None

if st.session_state.show_payment_modal and st.session_state.selected_checkout_plan:
    plan_name = st.session_state.selected_checkout_plan
    plan_price = PLANS[plan_name]["price"]
    
    st.markdown("--- ")
    st.subheader("💳 Selesaikan Pembayaran Anda")
    st.info(f"Anda memilih **Paket {plan_name}** dengan harga **Rp {plan_price:,} / bulan**.".replace(",", "."))
    
    payment_method = st.selectbox(
        "Pilih Metode Pembayaran:",
        ["Bank BCA", "Bank Mandiri", "Bank BNI", "Bank BTN", "Bank BRI", "QRIS"]
    )
    
    col_pay1, col_pay2 = st.columns(2)
    with col_pay1:
        if payment_method == "QRIS":
            st.markdown("**Metode QRIS (Scan QR Code):**")
            # Gunakan petik tiga (""") di awal dan akhir teks multiline
            st.code("""==============================
[ QRIS CODE IMAGE ]
SCAN UNTUK MEMBAYAR
==============================""")
            st.caption("Silakan scan QRIS di atas menggunakan aplikasi m-banking atau e-wallet Anda.")
            st.caption("Silakan scan QRIS di atas menggunakan aplikasi m-banking atau e-wallet Anda.")
        else:
            bank_recs = {
                "Bank BCA": "8012-3456-7890",
                "Bank Mandiri": "123-00-9876543-2",
                "Bank BNI": "0123-456-789",
                "Bank BTN": "4567-8901-2345-6",
                "Bank BRI": "0012-01-234567-50-9"
            }
            st.markdown(f"**Instruksi Transfer {payment_method}:**")
            st.write(f"Silakan transfer ke nomor rekening Virtual Account berikut:")
            st.info(f"🏛️ **{payment_method}**\n📌 No. Rekening: **{bank_recs[payment_method]}**\n👤 Atas Nama: **WAREHOUSE PREMIUM CO**")
    
    with col_pay2:
        st.markdown("**Rincian Transaksi:**")
        st.write(f"- Paket: **{plan_name}**")
        st.write(f"- Jumlah Tagihan: **Rp {plan_price:,}**".replace(",", "."))
        
        st.warning("Harap pastikan nominal transfer sesuai sebelum menekan tombol konfirmasi.")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Konfirmasi Pembayaran", type="primary", use_container_width=True):
                # Panggil fungsi upgrade ke backend
                res = upgrade_subscription(plan_name, 30)
                if res.get("status") != "error":
                    st.session_state.subscription_plan = plan_name
                    st.session_state.show_payment_modal = False
                    st.session_state.selected_checkout_plan = None
                    st.success(f"Pembayaran Berhasil! Paket Anda sekarang aktif sebagai {plan_name}.")
                    st.rerun()
                else:
                    st.error(f"Gagal memproses pembayaran: {res.get('message', 'Terjadi kesalahan')}")
        with col_btn2:
            if st.button("Batal", use_container_width=True):
                st.session_state.show_payment_modal = False
                st.session_state.selected_checkout_plan = None
                st.rerun()
    st.markdown("--- ")

active_plan = PLANS[st.session_state.subscription_plan]
product_count = len(items)
product_limit = active_plan["limit"]
st.info(
    f"Paket **{st.session_state.subscription_plan}** aktif · "
    + (f"{product_count} barang terdaftar · tanpa batas" if product_limit is None else
       f"{product_count} dari {product_limit} barang terpakai")
)

st.subheader("Ringkasan persediaan")
df = pd.DataFrame(items)
if not df.empty:
    left, right = st.columns([1.05, 1.4], gap="large")
    with left:
        st.markdown("#### Komposisi stok per kategori")
        category_stock = df.groupby("category", as_index=False)["quantity"].sum()
        chart = px.pie(category_stock, names="category", values="quantity", hole=.68,
                       color_discrete_sequence=["#087e75", "#f2a65a", "#4a90a4", "#8197ad", "#b7c9c5"])
        chart.update_traces(textposition="inside", textinfo="percent", insidetextfont=dict(color="white", size=12),
                            hovertemplate="%{label}<br>%{value} unit (%{percent})<extra></extra>")
        chart.update_layout(showlegend=True, legend=dict(orientation="h", y=-.12), margin=dict(l=10,r=10,t=10,b=25),
                            height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(family="DM Sans, sans-serif", color="#526574"),
                            annotations=[dict(text=f"{int(df['quantity'].sum())}<br><span style='font-size:11px'>unit</span>", x=.5,y=.5,showarrow=False,font=dict(size=21,color="#182b3a"))])
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.markdown("#### Produk dengan stok terbanyak")
        stock_view = df.nlargest(10, "quantity").sort_values("quantity", ascending=True)
        chart = px.bar(stock_view, x="quantity", y="name", orientation="h", color="status",
                       color_discrete_map={"NORMAL":"#168b7e", "LOW_STOCK":"#eba34a", "OUT_OF_STOCK":"#d9665d"},
                       labels={"quantity":"Jumlah stok", "name":"", "status":"Status"}, hover_data={"category":True, "unit":True, "status":True})
        chart.update_traces(marker_line_width=0, hovertemplate="%{y}<br>Stok: %{x}<extra></extra>")
        chart.update_layout(height=340, margin=dict(l=8,r=16,t=10,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(family="DM Sans, sans-serif", color="#526574"), xaxis=dict(showgrid=True, gridcolor="#edf1f3", zeroline=False),
                            yaxis=dict(showgrid=False), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})

    st.markdown("#### Daftar barang")
    st.dataframe(
        df[["sku", "name", "category", "quantity", "unit", "min_stock", "status"]],
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info("Belum ada data barang.")

st.subheader("Peringatan stok")
alerts = [item for item in items if item["status"] != "NORMAL"]
if alerts:
    st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
else:
    st.success("Semua barang memiliki stok yang cukup.")

with st.expander("＋ Tambah barang baru", expanded=False):
    if product_limit is not None and product_count >= product_limit:
        st.warning(f"Paket {st.session_state.subscription_plan} sudah mencapai batas {product_limit} barang. Pilih paket lain untuk menambah kapasitas.")
    else:
        with st.form("add_item_form"):
            sku = st.text_input("Kode barang (SKU)", placeholder="Contoh: BRG-001")
            name = st.text_input("Nama barang", placeholder="Contoh: Kardus ukuran sedang")
            category = st.text_input("Kategori", value="Umum")
            unit = st.text_input("Satuan", value="pcs")
            quantity = st.number_input("Stok awal", min_value=0, step=1)
            min_stock = st.number_input("Batas minimum stok", min_value=0, step=1)
            unit_price = st.number_input("Harga satuan (Rp)", min_value=0.0, step=1000.0)
            submitted = st.form_submit_button("Simpan barang", use_container_width=True)
            if submitted:
                if product_limit is not None and product_count >= product_limit:
                    st.error(f"Batas paket {st.session_state.subscription_plan} sudah tercapai.")
                else:
                    try:
                        api_post("/items", {
                            "sku": sku, "name": name, "category": category, "unit": unit,
                            "quantity": int(quantity), "min_stock": int(min_stock),
                            "unit_price": float(unit_price),
                        })
                        st.success("Barang berhasil ditambahkan.")
                        st.rerun()
                    except requests.RequestException as error:
                        st.error(f"Barang gagal disimpan: {error}")

with st.expander("⇄ Catat barang masuk atau keluar", expanded=False):
    if items:
        item_options = {f'{x["sku"]} - {x["name"]} (stok: {x["quantity"]})': x for x in items}
        with st.form("transaction_form"):
            selected = st.selectbox("Barang", list(item_options.keys()))
            transaction_type = st.selectbox("Jenis transaksi", ["IN", "OUT"], format_func=lambda kind: "Barang masuk" if kind == "IN" else "Barang keluar")
            transaction_qty = st.number_input("Jumlah", min_value=1, step=1)
            note = st.text_input("Catatan", placeholder="Opsional")
            tx_submit = st.form_submit_button("Simpan transaksi", use_container_width=True)
            if tx_submit:
                try:
                    result = api_post("/transactions", {
                        "item_id": item_options[selected]["id"],
                        "transaction_type": transaction_type,
                        "quantity": int(transaction_qty),
                        "note": note,
                    })
                    st.success(f'{result["message"]}. Stok baru: {result["new_stock"]}')
                except requests.HTTPError as error:
                    detail = error.response.text if error.response is not None else str(error)
                    st.error(f"Transaksi gagal: {detail}")
                except requests.RequestException as error:
                    st.error(f"Backend tidak dapat dihubungi: {error}")
    else:
        st.info("Tambahkan barang terlebih dahulu.")

st.subheader("🤖 AI Warehouse Assistant")
st.caption("AI membaca ringkasan stok dari database untuk membantu menjawab pertanyaan.")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Contoh: Barang apa yang perlu segera dibeli?")
if question:
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    inventory_context = pd.DataFrame(items).to_json(orient="records")
    
    system_prompt = """
    Kamu adalah Warehouse AI Assistant.

    Tugas kamu adalah membantu pengguna mengelola
    persediaan barang di gudang.

    Kemampuan:
    - Memeriksa jumlah stok.
    - Mengidentifikasi stok rendah.
    - Mengidentifikasi barang habis.
    - Memberikan rekomendasi pembelian.
    - Menganalisis kondisi persediaan.

    ATURAN WAJIB:
    1. Langsung berikan jawaban kepada pengguna.
    2. Jangan menulis analisis, monolog, atau narasi internal.
    3. Jangan mengulang pertanyaan pengguna.
    4. Jangan menulis kalimat seperti:
    "The user is asking..."
    "Let me check..."
    "I need to think..."
    "Okay, the user asked..."
    5. Gunakan bahasa Indonesia.
    6. Gunakan data inventory yang tersedia.
    7. Jangan mengarang informasi.
    8. Jawab maksimal 5 poin.
    9. Jika pertanyaan tidak berkaitan dengan inventory,
    jelaskan kemampuan Warehouse AI Assistant secara singkat.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt + "\n\nDATA INVENTORY:\n" + inventory_context
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # messages += st.session_state.chat_history[-6:]

    with st.chat_message("assistant"):
        answer = ""
        response_placeholder = st.empty()

        try:
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "stream": True,
                "keep_alive": "10m",
                "options": {
                    "temperature": 0.2,
                    "num_predict": 200,
                    "num_ctx": 4096
                }
            }
            with requests.post(
                OLLAMA_URL,
                json=payload,
                stream=True,
                timeout=(10, 300),
            ) as response:

                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    data = json.loads(line)
                    print("THINKING:", data.get("message", {}).get("thinking", ""))
                    print("CONTENT:", data.get("message", {}).get("content", ""))

                    # Ambil teks jawaban dari Ollama
                    content = data.get("message", {}).get("content", "")

                    if content:
                        answer += content
                        response_placeholder.markdown(answer + "▌")

                    # Berhenti jika proses sudah selesai
                    if data.get("done", False):
                        break

        except requests.exceptions.Timeout:
            answer = "Waktu tunggu habis. Coba gunakan model yang lebih ringan."

        except requests.exceptions.ConnectionError:
            answer = (
                "Tidak dapat terhubung ke Ollama. "
                "Pastikan container warehouse-ollama sedang berjalan."
            )

        except requests.exceptions.RequestException as e:
            answer = f"Terjadi kesalahan saat menghubungi Ollama: {e}"

        except Exception as e:
            answer = f"Terjadi kesalahan: {e}"

        response_placeholder.markdown(answer)

    st.session_state.chat_history.append(
        {"role": "assistant", "content": answer}
    )

if st.button("Reset Chat"):
    st.session_state.chat_history = []
    st.rerun()
