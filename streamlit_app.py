import openai
import os
import streamlit as st
import csv
from datetime import datetime
import base64
from io import BytesIO
import docx
import streamlit.components.v1 as components

def log_to_csv(prompt, generated_content):
    with open("lesson_plan_logs.csv", mode="a", newline="", encoding="utf-8") as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow([datetime.now(), prompt, generated_content])

def extract_contents_from_docx(docx_file):
    document = docx.Document(docx_file)
    contents = []

    for block in document._element.body:
        if block.tag.endswith("tbl"):
            table = docx.table.Table(block, document)
            table_text = convert_table_to_text(table)
            contents.append({"type": "table", "text": table_text})
        else:
            for para in block.xpath(".//w:p"):
                para = docx.text.paragraph.Paragraph(para, document)
                if para.style.name.startswith("Heading"):
                    contents.append({"type": "heading", "text": para.text, "style": para.style.name})
                else:
                    contents.append({"type": "paragraph", "text": para.text})

    return contents

def convert_table_to_text(table):
    table_text = ""
    for row in table.rows:
        for cell in row.cells:
            table_text += cell.text + "\t"
        table_text += "\n"
    return table_text

def generate_content_from_template(template_contents, user_prompt):
    openai.api_key = os.environ["OPENAI_API_KEY"]

    full_prompt = f"Please generate a lesson plan based on the following template and user prompt:\n\nUser Prompt: {user_prompt}\n\nTemplate:\n\n"
    for item in template_contents:
        if item["type"] == "heading":
            full_prompt += f"\n{item['text']} ({item['style']})\n"
        elif item["type"] == "paragraph":
            full_prompt += f"{item['text']} "
        else:  # item["type"] == "table"
            full_prompt += "\n[Table]\n" + item["text"]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that can generate lesson plans based on a template and user prompt."
                ),
            },
            {"role": "user", "content": full_prompt},
        ],
        max_tokens=2000,
        n=1,
        stop=None,
        temperature=0.7,
    )

    generated_content = response["choices"][0]["message"]["content"].split("\n\n")

    return generated_content

def docx_from_generated_content(template_contents, generated_content):
    document = docx.Document()

    for i, item in enumerate(template_contents):
        if item["type"] == "heading":
            document.add_heading(generated_content[i], level=int(item["style"][-1]))
        elif item["type"] == "paragraph":
            document.add_paragraph(generated_content[i])
        else:  # item["type"] == "table"
            # TODO: Add logic to recreate table structure and add generated content

    return document

st.title("Lesson Plan Generator from DOCX Template")

uploaded_file = st.file_uploader("Upload a DOCX file", type=["docx"])
user_prompt = prompt = st.text_input("Enter a prompt to guide the content generation:")

if st.button("Generate Lesson Plan"):
    if uploaded_file:
        with st.spinner("Generating..."):
            template_contents = extract_contents_from_docx(uploaded_file)
            generated_content = generate_content_from_template(template_contents, user_prompt)

            docx_document = docx_from_generated_content(template_contents, generated_content)

            buffer = BytesIO()
            docx_document.save(buffer)
            buffer.seek(0)

            b64 = base64.b64encode(buffer.getvalue()).decode()

            st.download_button(
                label="Download Generated Lesson Plan",
                data=buffer,
                file_name=f"generated_lesson_plan.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

            log_to_csv(full_prompt, generated_content)
    else:
        st.warning("Please upload a DOCX file.")
