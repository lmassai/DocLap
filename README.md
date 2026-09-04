# DocLap 1.0 (Document Layout Parser)

## Citation

If you use DocLap or the resources in this repository, please cite the following paper:

**APA Style:**
Massai, L., & Marinai, S. (2027). The DocLap integrated system for understanding multi-page scholarly documents. *Expert Systems with Applications*, 333, 133839. https://doi.org

**BibTeX:**
```bibtex
@article{MASSAI2027133839,
  author    = {Lorenzo Massai and Simone Marinai},
  title     = {The DocLap integrated system for understanding multi-page scholarly documents},
  journal   = {Expert Systems with Applications},
  volume    = {333},
  pages     = {133839},
  year      = {2027},
  issn      = {0957-4174},
  doi       = {10.1016/j.eswa.2026.133839},
  url       = {https://sciencedirect.com}
}
```

**APA Style:**
Massai, L., & Marinai, S. (2026). The DocLap interface for document layout analysis and interaction. In Proceedings of ECML PKDD 2026. Springer.

**BibTeX:**
```bibtex
@inproceedings{MASSAI2026DOCLAP,
  author    = {Lorenzo Massai and Simone Marinai},
  title     = {The DocLap interface for document layout analysis and interaction},
  booktitle = {Proceedings of ECML PKDD 2026},
  year      = {2026},
  publisher = {Springer},
  address   = {Napoli, Italy},
  pages     = {0--0},
  month     = sep
}
```

## Overview

Computational understanding of documents is focused on visual and text analysis, building upon computer vision and natural language processing. With the advent of transformers document understanding is even more shifted from the actual comprehension of documents, which relies on concurrent perception of text, layout elements and document structure, to convoluted feature representations. Recent trends for providing unified access to such representations go towards Large Language Models (LLMs). However, these models have limitations: they lack explainability, demand significant resources for training and inference, and are not well suited for processing extensive inputs nor for direct application in specialized domains.
This paper aims at creating a comprehensive interface for document analysis, enabling multi-layered exploration and integrating diverse features and contextual information. By bridging diverse information, our work pursues the identification, characterization, and linking of visual elements to semantic and contextual data, leveraging LLMs for interoperability. This enables a unified access to textual, visual, and structural layers, embedding levels of structured knowledge directly in the LLM context. Recent advances in Retrieval-Augmented Generation (RAG) are also exploited to address some LLM limitations related to context length, allowing access to latent information from document representations such as graph and vector embeddings. The association of structural information to visual data allows formal analysis of documents and is exploited in our model to enhance visual recognition, improved through multi-modal LLM correction supported by ontology-based constraint violation detection. The framework enables semantic retrieval over extracted information, providing direct access to the document structure which can be exploited in many applications such as Question Answering (QA) and document understanding.
As a result of this work, the DocLap (Document Layout Parser) system for document analysis and retrieval is proposed, which enables the extraction of visual and semantic features from documents and makes them accessible through natural language in an integrated framework providing conversational reasoning. The system’s segmentation, error detection, and information retrieval capabilities are extensively evaluated through experiments.are increasingly used for document understanding, they often lack explainability, demand heavy computational resources, and struggle with long, specialized academic texts. DocLap bridges this gap by creating a comprehensive interface that connects visual layout recognition with semantic and contextual data. By embedding multi-layered structural knowledge directly into the LLM context and leveraging Retrieval-Augmented Generation (RAG), the system enables conversational reasoning and precise Question Answering (QA) over complex document structures.

## Features

* **Multi-Layered Document Exploration:** Integrates textual, visual, and structural data layers to provide a unified access point for document understanding.
* **Advanced Layout Parsing & Segmentation:** Identifies, characterizes, and links visual elements to semantic information, overcoming the limitations of traditional feature representations.
* **Graph & Vector RAG Integration:** Utilizes Retrieval-Augmented Generation supported by graph and vector embeddings to extract latent information without hitting LLM context length limits.
* **Ontology-Based Error Correction:** Enhances visual recognition accuracy through multi-modal LLM correction backed by automated ontology constraint violation detection.
* **Conversational Reasoning & QA:** Enables semantic retrieval over extracted data, allowing users to query and interact with complex scholarly documents using natural language.

## Installation
1. Use Python 3.13 and add it to system path
2. The dependency "fitz" is not the name of the package to download. PyMuPDF is the correct package.
3. Poppler (https://poppler.freedesktop.org/) must be installed, and its path has to be added to the O.S. path variable.
4. Ollama MUST be installed (https://ollama.com/download), otherwise the LLM part will not work.
5. ```ollama run gpt-oss:120b-cloud``` must be executed the first time to pull the model.
6. ```ollama run qwen3-vl:235b-cloud``` must be executed the first time to pull the model.
7. LaTeXML MUST be installed (otherwise the LaTeX part will not work) from: https://math.nist.gov/~BMiller/LaTeXML/get.html
8. When installing LaTeXML, it must be installed without tests, using:
```
cpan -T LaTeXML
```
9. Follow the instructions for Strawberry Perl from PowerShell with administrator privileges (NOT Choco),
also installing ImageMagick from: https://imagemagick.org/script/download.php.
10. Add the LaTeXML and ImageMagick paths to the O.S. path variable.

## Usage
1. Execute in terminal and keep alive:  ```ollama run gpt-oss:120b-cloud``` and ```ollama run llava```
2. To run the server, from the project folder launch:
```
python api_server.py
```
3. To enable the interface:
```
python -m http.server
```
4. Open in browser:
```
http://localhost:8000/webpages/index.html
```







