import requests
import base64
import re

def extract_bounding_boxes(raw_lines):
    result = []
    for line in raw_lines:
        parts = line.strip().split(',')
        if len(parts) >= 6:
            label = parts[0].strip()
            page = parts[1].strip()
            x = parts[2]
            y = parts[3]
            w = parts[4]
            h = parts[5]
            result.append(f"{label},{page},{x},{y},{w},{h}")
    return result

def clean_answer(raw_answer, allowed_classes):
    pattern = r"([\w ]+),\d+,(?:\d+\.\d+|\d+),(?:\d+\.\d+|\d+),(?:\d+\.\d+|\d+),(?:\d+\.\d+|\d+)"

    results = []

    for match in re.finditer(pattern, raw_answer):
        full_string = match.group(0)
        layout_class = match.group(1).strip()
        if layout_class in allowed_classes:
            results.append(full_string)

    return "\n".join(results) if results else "Invalid output"

def ask_to_LLaVA(lines, image_path):

    question = (
        "Given the attached image, which represents a page from a research article, it contains some overlapping "
        "bounding boxes, each associated with a label and coordinates in the format: label,page,x,y,w,h. The label and coordinates "
        f"of two of the overlaps are given below:\n{lines}\nFor each block, one of the two is correct, the other is "
        "WRONG. The goal is to verify which block is wrong. Correct means that it encloses only the expected "
        "content defined by the label (neither too much nor too little). Return ONLY the WRONG bounding box in the format "
        "label,page,x,y,w,h. When giving the output please double-check that the block that you give is "
        "one of the two given as input, without any change neither in the label nor in the numbers. No explanation, no "
        "extra text, no comments."
    )
    print("\nQuestion given to to Qwen:\n" + question + "\n")

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": "qwen3-vl:235b-cloud",
        "prompt": question,
        "images": [image_data],  # lista di base64 come prima
        "temperature": 0,
        "stream": False
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload)

    if response.status_code == 200:
        answer = response.json()["response"]

        allowed_classes = [
            "Article_title", "Author", "Abstract", "Caption_Figure", "Caption_Table", "Caption", "Figure", "Table", "Formula", "Section", "Link", "Note", "Acknowledgements", "Reference"
        ]
        cleaned = clean_answer(answer, allowed_classes)

        print(f"- Answer: {answer}")

        return cleaned.lstrip()
    else:
        print("Error in response:", response.text)
        return None

