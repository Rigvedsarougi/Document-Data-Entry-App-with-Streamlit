import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import uuid
import json
from pdf2image import convert_from_bytes
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import tempfile

# Constants
FIELD_TYPES = ["Text", "Image", "Signature"]
DEFAULT_FONT_SIZE = 12
TEMPLATE_DIR = "templates"

# Create template directory if not exists
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# Initialize session state
def init_session_state():
    if "fields" not in st.session_state:
        st.session_state.fields = []
    if "current_field" not in st.session_state:
        st.session_state.current_field = None
    if "mode" not in st.session_state:
        st.session_state.mode = "layout"  # or "input"
    if "document_image" not in st.session_state:
        st.session_state.document_image = None
    if "document_pages" not in st.session_state:
        st.session_state.document_pages = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0
    if "template_name" not in st.session_state:
        st.session_state.template_name = ""
    if "field_values" not in st.session_state:
        st.session_state.field_values = {}

init_session_state()

# Helper functions
def convert_pdf_to_images(pdf_file):
    return convert_from_bytes(pdf_file.read())

def save_template():
    if not st.session_state.template_name:
        st.warning("Please enter a template name")
        return
    
    template_path = os.path.join(TEMPLATE_DIR, f"{st.session_state.template_name}.json")
    template_data = {
        "fields": st.session_state.fields,
        "document_type": "pdf" if uploaded_file.name.lower().endswith(".pdf") else "image"
    }
    
    with open(template_path, "w") as f:
        json.dump(template_data, f)
    
    st.success(f"Template '{st.session_state.template_name}' saved successfully!")

def load_template(template_name):
    template_path = os.path.join(TEMPLATE_DIR, f"{template_name}.json")
    with open(template_path, "r") as f:
        template_data = json.load(f)
    
    st.session_state.fields = template_data["fields"]
    st.success(f"Template '{template_name}' loaded successfully!")

def delete_template(template_name):
    template_path = os.path.join(TEMPLATE_DIR, f"{template_name}.json")
    if os.path.exists(template_path):
        os.remove(template_path)
        st.success(f"Template '{template_name}' deleted successfully!")
    else:
        st.warning("Template not found")

def get_available_templates():
    return [f.replace(".json", "") for f in os.listdir(TEMPLATE_DIR) if f.endswith(".json")]

def create_pdf_with_fields():
    if not st.session_state.document_pages:
        st.warning("No document loaded")
        return None
    
    # For multi-page PDFs, we'll just use the first page for this example
    img = st.session_state.document_pages[st.session_state.current_page]
    
    # Create a new image with the fields
    img_with_fields = img.copy()
    draw = ImageDraw.Draw(img_with_fields)
    
    try:
        font = ImageFont.truetype("arial.ttf", DEFAULT_FONT_SIZE)
    except:
        font = ImageFont.load_default()
    
    for field in st.session_state.fields:
        if field["page"] != st.session_state.current_page:
            continue
            
        value = st.session_state.field_values.get(field["alias"], "")
        
        if field["type"] == "Text":
            draw.rectangle(
                [field["x"], field["y"], field["x"] + field["width"], field["y"] + field["height"]],
                outline="red",
                width=1
            )
            draw.text((field["x"], field["y"]), str(value), fill="black", font=font)
        elif field["type"] == "Signature":
            draw.rectangle(
                [field["x"], field["y"], field["x"] + field["width"], field["y"] + field["height"]],
                outline="blue",
                width=1
            )
            if value:  # Assuming value is an image for signature
                try:
                    signature_img = Image.open(io.BytesIO(value))
                    signature_img = signature_img.resize((field["width"], field["height"]))
                    img_with_fields.paste(signature_img, (field["x"], field["y"]))
                except:
                    draw.text((field["x"], field["y"]), "Signature", fill="black", font=font)
        elif field["type"] == "Image":
            draw.rectangle(
                [field["x"], field["y"], field["x"] + field["width"], field["y"] + field["height"]],
                outline="green",
                width=1
            )
            if value:  # Assuming value is an image
                try:
                    field_img = Image.open(io.BytesIO(value))
                    field_img = field_img.resize((field["width"], field["height"]))
                    img_with_fields.paste(field_img, (field["x"], field["y"]))
                except:
                    draw.text((field["x"], field["y"]), "Image", fill="black", font=font)
    
    # Convert to PDF
    pdf_bytes = io.BytesIO()
    img_with_fields.save(pdf_bytes, format="PDF")
    pdf_bytes.seek(0)
    
    return pdf_bytes

# UI Layout
st.title("Document Data Entry App")

# Mode selection
col1, col2 = st.columns(2)
with col1:
    if st.button("Layout Mode"):
        st.session_state.mode = "layout"
with col2:
    if st.button("Input Mode"):
        st.session_state.mode = "input"

st.write(f"Current mode: **{st.session_state.mode.upper()}**")

# Document upload
uploaded_file = st.file_uploader("Upload Document (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    if uploaded_file.name.lower().endswith(".pdf"):
        st.session_state.document_pages = convert_pdf_to_images(uploaded_file)
    else:
        st.session_state.document_pages = [Image.open(uploaded_file)]
    
    st.session_state.document_image = st.session_state.document_pages[0]
    
    # Show page selector for multi-page PDFs
    if len(st.session_state.document_pages) > 1:
        st.session_state.current_page = st.selectbox(
            "Select Page",
            range(len(st.session_state.document_pages)),
            index=st.session_state.current_page
        )
        st.session_state.document_image = st.session_state.document_pages[st.session_state.current_page]

# Template management
st.sidebar.header("Template Management")
st.session_state.template_name = st.sidebar.text_input("Template Name")

col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("Save Template"):
        save_template()
with col2:
    if st.button("Load Template"):
        available_templates = get_available_templates()
        if available_templates:
            selected_template = st.selectbox("Select Template", available_templates)
            load_template(selected_template)
with col3:
    if st.button("Delete Template"):
        available_templates = get_available_templates()
        if available_templates:
            selected_template = st.selectbox("Select Template to Delete", available_templates, key="delete_select")
            delete_template(selected_template)

# Layout Mode
if st.session_state.mode == "layout" and st.session_state.document_image:
    st.subheader("Layout Mode - Add Fields to Document")
    
    # Field properties form
    with st.expander("Add New Field"):
        field_type = st.selectbox("Field Type", FIELD_TYPES, key="field_type")
        alias = st.text_input("Field Alias/Label", key="field_alias")
        width = st.number_input("Width", min_value=20, max_value=500, value=100, key="field_width")
        height = st.number_input("Height", min_value=20, max_value=500, value=30, key="field_height")
        
        if st.button("Add Field"):
            new_field = {
                "id": str(uuid.uuid4()),
                "type": field_type,
                "alias": alias,
                "x": 50,
                "y": 50,
                "width": width,
                "height": height,
                "page": st.session_state.current_page
            }
            st.session_state.fields.append(new_field)
            st.session_state.current_field = new_field["id"]
            st.success(f"Added {field_type} field: {alias}")
    
    # Display document with fields
    st.subheader("Document Preview with Fields")
    
    # Create a canvas to display the document and fields
    img = st.session_state.document_image.copy()
    draw = ImageDraw.Draw(img)
    
    for field in st.session_state.fields:
        if field["page"] != st.session_state.current_page:
            continue
            
        color = "red" if field["type"] == "Text" else "green" if field["type"] == "Image" else "blue"
        draw.rectangle(
            [field["x"], field["y"], field["x"] + field["width"], field["y"] + field["height"]],
            outline=color,
            width=2
        )
        draw.text((field["x"], field["y"] - 15), field["alias"], fill=color)
    
    st.image(img, use_column_width=True)
    
    # Field position adjustment
    if st.session_state.fields:
        st.subheader("Field Position Adjustment")
        selected_field = st.selectbox(
            "Select Field to Adjust",
            [f"{f['alias']} ({f['type']})" for f in st.session_state.fields if f["page"] == st.session_state.current_page],
            index=0
        )
        
        selected_field_index = next(
            i for i, f in enumerate(st.session_state.fields)
            if f"{f['alias']} ({f['type']})" == selected_field and f["page"] == st.session_state.current_page
        )
        
        col1, col2 = st.columns(2)
        with col1:
            new_x = st.number_input("X Position", value=st.session_state.fields[selected_field_index]["x"])
        with col2:
            new_y = st.number_input("Y Position", value=st.session_state.fields[selected_field_index]["y"])
        
        if st.button("Update Position"):
            st.session_state.fields[selected_field_index]["x"] = new_x
            st.session_state.fields[selected_field_index]["y"] = new_y
            st.success("Position updated!")
        
        if st.button("Delete Field"):
            del st.session_state.fields[selected_field_index]
            st.success("Field deleted!")

# Input Mode
elif st.session_state.mode == "input" and st.session_state.document_image and st.session_state.fields:
    st.subheader("Input Mode - Enter Data for Fields")
    
    # Display document preview with field areas marked
    img = st.session_state.document_image.copy()
    draw = ImageDraw.Draw(img)
    
    for field in st.session_state.fields:
        if field["page"] != st.session_state.current_page:
            continue
            
        color = "red" if field["type"] == "Text" else "green" if field["type"] == "Image" else "blue"
        draw.rectangle(
            [field["x"], field["y"], field["x"] + field["width"], field["y"] + field["height"]],
            outline=color,
            width=2
        )
        draw.text((field["x"], field["y"] - 15), field["alias"], fill=color)
    
    st.image(img, use_column_width=True, caption="Document with field locations")
    
    # Input form for each field
    with st.form("data_input_form"):
        for field in st.session_state.fields:
            if field["page"] != st.session_state.current_page:
                continue
                
            if field["type"] == "Text":
                st.session_state.field_values[field["alias"]] = st.text_input(
                    f"{field['alias']} (Text)",
                    value=st.session_state.field_values.get(field["alias"], "")
                )
            elif field["type"] == "Signature":
                st.session_state.field_values[field["alias"]] = st.file_uploader(
                    f"{field['alias']} (Signature Image)",
                    type=["png", "jpg", "jpeg"],
                    key=f"signature_{field['alias']}"
                )
                if st.session_state.field_values[field["alias"]]:
                    st.session_state.field_values[field["alias"]] = st.session_state.field_values[field["alias"]].read()
            elif field["type"] == "Image":
                st.session_state.field_values[field["alias"]] = st.file_uploader(
                    f"{field['alias']} (Image)",
                    type=["png", "jpg", "jpeg"],
                    key=f"image_{field['alias']}"
                )
                if st.session_state.field_values[field["alias"]]:
                    st.session_state.field_values[field["alias"]] = st.session_state.field_values[field["alias"]].read()
        
        submitted = st.form_submit_button("Generate Final Document")
        
        if submitted:
            final_pdf = create_pdf_with_fields()
            if final_pdf:
                st.success("Document generated successfully!")
                st.download_button(
                    label="Download Final Document",
                    data=final_pdf,
                    file_name="filled_document.pdf",
                    mime="application/pdf"
                )
else:
    st.info("Upload a document and add fields in Layout Mode first.")
