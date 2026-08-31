import streamlit as st
from pypdf import PdfWriter
import io
from PIL import Image
import zipfile
import fitz  # ไลบรารี PyMuPDF สำหรับแปลง PDF เป็นภาพ

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="My PDF Tools", page_icon="📄", layout="wide")

# ==========================================
# จัดการสถานะของเมนู (ทำให้กดปุ่มแล้วหน้าเปลี่ยน)
# ==========================================
if 'menu' not in st.session_state:
    st.session_state.menu = "รวมไฟล์ PDF"

st.sidebar.title("🛠️ เลือกเครื่องมือ")

# สร้างปุ่มแบบเหลี่ยมเต็มความกว้าง (use_container_width=True)
if st.sidebar.button("🗂️ รวมไฟล์ PDF", use_container_width=True):
    st.session_state.menu = "รวมไฟล์ PDF"
if st.sidebar.button("🖼️ รวมภาพเป็น PDF", use_container_width=True):
    st.session_state.menu = "รวมภาพเป็น PDF"
if st.sidebar.button("✂️ แยกหน้า PDF เป็นภาพ", use_container_width=True):
    st.session_state.menu = "แยกหน้า PDF"

menu = st.session_state.menu

# ==========================================
# 1. ฟังก์ชันรวมไฟล์ PDF
# ==========================================
if menu == "รวมไฟล์ PDF":
    st.title("🗂️ รวมไฟล์ PDF")
    st.write("อัปโหลดไฟล์ PDF หลายๆ ไฟล์ เพื่อนำมารวมเป็นไฟล์เดียว (เรียงตามลำดับ)")

    uploaded_files = st.file_uploader("เลือกไฟล์ PDF", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        st.info(f"📂 เลือกแล้ว {len(uploaded_files)} ไฟล์")
        if st.button("รวมไฟล์ PDF"):
            merger = PdfWriter()
            for pdf_file in uploaded_files:
                merger.append(pdf_file)
                
            output_pdf = io.BytesIO()
            merger.write(output_pdf)
            
            st.success("✅ รวมไฟล์สำเร็จ!")
            st.download_button("⬇️ ดาวน์โหลด PDF ที่รวมแล้ว", data=output_pdf.getvalue(), file_name="merged_output.pdf", mime="application/pdf")

# ==========================================
# 2. ฟังก์ชันแปลงภาพเป็น PDF (รองรับสูงสุด 400MB ตามที่รันใน Terminal)
# ==========================================
elif menu == "รวมภาพเป็น PDF":
    st.title("🖼️ รวมภาพเป็น PDF")
    st.write("อัปโหลดไฟล์รูปภาพ (JPG, PNG) หลายๆ ไฟล์ เพื่อแปลงและรวมเป็นไฟล์ PDF เดียว (รองรับไฟล์สูงสุด 400 MB)")
    
    uploaded_images = st.file_uploader("เลือกรูปภาพ", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    
    if uploaded_images:
        st.info(f"🖼️ เลือกแล้ว {len(uploaded_images)} ภาพ")
        if st.button("สร้าง PDF จากรูปภาพ"):
            images = []
            for img_file in uploaded_images:
                img = Image.open(img_file).convert('RGB')
                images.append(img)
            
            if images:
                output_pdf = io.BytesIO()
                images[0].save(output_pdf, format="PDF", save_all=True, append_images=images[1:])
                st.success("✅ แปลงรูปภาพเป็น PDF สำเร็จ!")
                st.download_button("⬇️ ดาวน์โหลดไฟล์ PDF", data=output_pdf.getvalue(), file_name="images_to_pdf.pdf", mime="application/pdf")

# ==========================================
# 3. ฟังก์ชันแยกหน้า PDF ออกมาเป็น "รูปภาพ (PNG)"
# ==========================================
elif menu == "แยกหน้า PDF":
    st.title("✂️ แยกหน้า PDF ออกเป็นรูปภาพ")
    st.write("อัปโหลดไฟล์ PDF 1 ไฟล์ ระบบจะแยกแต่ละหน้าออกมาเป็นไฟล์รูปภาพ (.png) แล้วรวมเป็นไฟล์ ZIP ให้ดาวน์โหลด")
    
    uploaded_pdf = st.file_uploader("เลือกไฟล์ PDF ที่ต้องการแยก", type="pdf")
    
    if uploaded_pdf:
        # อ่านไฟล์ PDF ด้วย PyMuPDF
        pdf_bytes = uploaded_pdf.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        
        st.info(f"📄 ไฟล์นี้มีทั้งหมด {total_pages} หน้า")
        
        if st.button("แปลงแต่ละหน้าเป็นรูปภาพ"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # สร้าง Progress Bar ให้ดูตอนกำลังแปลงไฟล์
                progress_bar = st.progress(0)
                
                for i in range(total_pages):
                    page = doc.load_page(i)
                    # แปลงหน้า PDF เป็นภาพ (dpi=150 เพื่อความคมชัดกำลังดี ไม่หนักเกินไป)
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    
                    # บันทึกภาพลงใน ZIP
                    zip_file.writestr(f"page_{i+1}.png", img_bytes)
                    
                    # อัปเดตแถบความคืบหน้า
                    progress_bar.progress((i + 1) / total_pages)
            
            st.success("✅ แปลงและบีบอัดเป็น ZIP สำเร็จ!")
            st.download_button(
                label="⬇️ ดาวน์โหลดไฟล์ ZIP (รูปภาพทุกหน้า)",
                data=zip_buffer.getvalue(),
                file_name="pdf_to_images.zip",
                mime="application/zip"
            )