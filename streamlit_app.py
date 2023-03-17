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

def generate_content_from_template(user_prompt):
    openai.api_key = os.environ["OPENAI_API_KEY"]

    full_prompt = f"""
Please generate a lesson plan based on the template below, following the user prompt. Modify the template to include specific steps, activities, time allocation, and any additional aspects needed to create a comprehensive lesson plan.

User Prompt: {user_prompt}

Template:

I. Introduction
- Greetings and warm-up activities

II. Vocabulary/ Grammar
- Introduce new vocabulary and/or grammar structures

III. Practice Activities
- Activities to reinforce new vocabulary and/or grammar structures, such as:
  a. Role-plays
  b. Reading comprehension exercises
  c. Listening comprehension exercises
  d. Writing exercises

IV. Review
- Review vocabulary and/or grammar covered in the class

V. Reflection
- Possible reflection questions or activities to encourage students to reflect on what they have learned

VI. Homework
- Assign homework to reinforce the concepts learned in class

VII. Closing
- Farewells and class dismissal

Note: The time for activities may vary depending on the level of the class and the complexity of the concepts being taught. Additionally, the lesson plan may include specific materials needed for each activity, such as textbooks, audio or video resources, and worksheets.
"""

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

def docx_from_generated_content(generated_content):
    document = docx.Document()

    for i, item in enumerate(generated_content):
        if i == 0:
            document.add_heading(item, level=1)
        else:
            document.add_heading(item.split("\n")[0], level=2)
            document.add_paragraph(item.split("\n", 1)[1].strip())

    return document

st.title("Lesson Plan Generator")

user_prompt = st.text_input("Enter a prompt to guide the content generation:")

if st.button("Generate Lesson Plan"):
    with st.spinner("Generating..."):
        generated_content = generate_content_from_template(user_prompt)

        docx_document = docx_from_generated_content(generated_content)

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

        log_to_csv(user_prompt, generated_content)
