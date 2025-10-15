# DocLap 1.0 (Document Layout Parser)

## Installation
1. Use Python 3.13 and add it to system path
2. The dependency "fitz" is not the name of the package to download. PyMuPDF is the correct package.
3. Poppler (https://poppler.freedesktop.org/) MUST be installed, and its path has to be added to the O.S. path variable.
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






