# **The Neural Document Parsing Revolution: A Global Survey of Conversion Frameworks and Model Ecosystems (March 2026\)**

The landscape of document format conversion has undergone a definitive **structural transition between 2024 and 2026**, moving from classical, heuristic-based optical character recognition (OCR) toward **unified vision-language models (VLMs).** This shift is primarily dictated by the requirements of the Retrieval-Augmented Generation **(RAG) and AI agent ecosystems**, where the objective of conversion is **no longer mere text extraction** but the **high-fidelity reconstruction of semantic hierarchy**.1 As of March 29, 2026, the ecosystem is characterized by the **dominance of "hybrid engines"** that combine direct text extraction with neural layout analysis to **mitigate hallucinations** while maintaining **structural integrity**.2

## **Section 1: Open-Source Document Conversion Tools**

The **open-source community** remains the **primary engine of innovation** in the document parsing space, with several projects achieving massive scale in both developer adoption and technical complexity. The governance of these projects has evolved from individual contributions to formal backing by global technology leaders like **Microsoft, IBM, and Hancom**.3

### **A. Universal/Multi-Format Converters**

These frameworks are designed as comprehensive entry points for disparate data sources, prioritizing ease of use and broad compatibility.

**MarkItDown (Microsoft)**

* **Repository and Metrics**: [microsoft/markitdown](https://github.com/microsoft/markitdown); \~93,000 stars; \~4,000 forks; MIT License; Last commit: March 2026; Latest Version: v0.1.5.5  
* **Backing**: Microsoft Research / AutoGen Team.  
* **Input Formats**: PDF, PowerPoint (PPTX), Word (DOCX), Excel (XLSX), Images (JPG, PNG, TIFF), Audio (WAV, MP3), YouTube URLs, HTML, Text, ZIP, EPub, RTF.5  
* **Output Formats**: Markdown (CommonMark/GFM).  
* **Technical Differentiator**: MarkItDown integrates **Microsoft's Magika** for high-accuracy **MIME type detection** and leverages speech-to-text models for **transcribing audio/video** components directly into the document stream.5  
* **Limitations**: It is often characterized as a **"lightweight" utility**; while it excels at quick text extraction, it **lacks the advanced neural layout analysis** found in specialized PDF parsers, leading to potential loss of structural fidelity in complex multi-column documents.8  
* **Install**: pip install 'markitdown\[all\]'.7

**Docling (IBM Research)**

* **Repository and Metrics**: [docling-project/docling](https://github.com/docling-project/docling); \~57,000 stars; \~3,900 forks; MIT License; Last commit: March 2026; Latest Version: v2.82.0.6  
* **Backing**: IBM Research; Governance: Hosted by the LF AI & Data Foundation.9  
* **Input Formats**: PDF, DOCX, PPTX, XLSX, HTML, Images, LaTeX, XBRL, WebVTT, Plain Text, Audio.6  
* **Output Formats**: Markdown, JSON, HTML, WebVTT, DocTags.6  
* **Technical Differentiator**: Docling utilizes the **proprietary "Heron" layout model** for accelerated parsing and the **TableFormer architecture** for precise table reconstruction. It is uniquely compatible with the **Granite-Docling** series of **VLMs**.6  
* **Limitations**: High resource requirements for full VLM pipelines; Python 3.9 support was officially dropped in version 2.70.0 (requires 3.10+).6  
* **Install**: pip install docling.6

### **B. PDF-Specialized Frameworks**

The complexity of the PDF format necessitates tools that **combine low-level file parsing with high-level computer vision**.

**MinerU (OpenDataLab)**

* **Repository and Metrics**: [opendatalab/mineru](https://github.com/opendatalab/mineru); \~57,500 stars; \~4,800 forks; AGPL-3.0 License; Last commit: March 2026; Latest Version: v2.7.6.2  
* **Backing**: OpenDataLab (Tsinghua University & Shanghai AI Lab).8  
* **Input Formats**: PDF (Native text and scanned), DOCX, Images.  
* **Output Formats**: Markdown, JSON.  
* **Technical Differentiator**: Features a "**hybrid backend**" released in late 2025 that integrates **direct text extraction** with **VLM-guided layout anchors**. This approach drastically reduces "**parsing hallucinations**" common in pure vision-based models.2  
* **Limitations**: **AGPL-3.0** license requirements may impede certain commercial proprietary integrations; **heavy dependency stack**.2  
* **Install**: uv pip install mineru\[all\].2

**OpenDataLoader PDF (Hancom)**

* **Repository and Metrics**: [hancom-io/opendataloader](https://github.com/hancom-io/opendataloader); \~7,000 stars; \~500 forks; Apache 2.0 License; Last commit: March 2026; Latest Version: v2.0.3  
* **Backing**: Hancom and DualLab.3  
* **Input Formats**: PDF (Complex structures).  
* **Output Formats**: Markdown, JSON, XML.  
* **Technical Differentiator**: A **security-first** local engine that reached \#1 on GitHub trending in March 2026\. It includes built-in **AI add-ons for chart analysis and formula** extraction that operate entirely on-premise.3  
* **Limitations**: Newer entry compared to Docling; community ecosystem still in early rapid expansion phase.3  
* **Install**: Available via official GitHub repository (March 2026).12

### **C. Office and Data Specialized**

**Unstructured.io**

* **Repository and Metrics**: [unstructured-io/unstructured](https://github.com/unstructured-io/unstructured); \~14,000 stars; \~1,200 forks; Apache 2.0 License; Latest Version: v0.22.4.14  
* **Features**: Specialized in "**partitioning" diverse formats** (PDF, HTML, Word, Email) into a unified element-based schema for LLM ingestion.15  
* **Updates**: Version 0.22.4 (Feb 2026\) introduced **audio speech-to-text partitioning** and optimized PDF rendering via PyPDFium2.14  
* **Install**: pip install unstructured.15

### **D. Summary Table of Open-Source Tools**

| Tool | Backer | License | Primary Differentiator | Recency |
| :---- | :---- | :---- | :---- | :---- |
| MarkItDown | Microsoft | MIT | Audio/Video/YouTube support | v0.1.5 (Feb 2026\) 5 |
| Docling | IBM | MIT | Heron layout model; DocTags | v2.82.0 (Mar 2026\) 6 |
| MinerU | OpenDataLab | AGPL-3.0 | Hybrid direct/VLM engine | v2.7.6 (Feb 2026\) 2 |
| OpenDataLoader | Hancom | Apache 2.0 | Local security; chart analysis | v2.0 (Mar 2026\) 3 |
| Marker | Vik Paruchuri | GPL-3.0 | High-throughput (25 pps) | v0.3.3 (Mar 2026\) 17 |
| PyMuPDF4LLM | Artifex | GNU AFFERO | Extreme speed (native text) | v0.0.2 (2026) 18 |

## **Section 2: Commercial Document Processing Services**

Commercial platforms in 2026 have shifted toward "**Agentic OCR,"** offering **iterative correction loops and deep integration with cloud-native RAG** frameworks. These services prioritize **high-volume reliability, security compliance (SOC2/HIPAA), and specialized domain processors.**1

### **A. Major Cloud Provider APIs**

**Google Document AI**

* **Pricing**: **Enterprise OCR** is billed at $1.50 per 1,000 pages for the first 5 million pages, dropping to $0.60 per 1,000 pages thereafter.19 **Specialized processors** like the **Form Parser or Custom Extractor** cost $30 per 1,000 pages.19  
* **Capabilities**: Integrates **Gemini 1.5 Pro** for massive document sets; offers **specialized** processors for **invoices, receipts, and identity documents**.1  
* **Limits**: **Synchronous** requests are limited to **15 pages**; **batch** requests support up to **200** pages per document.19

**AWS Textract**

* **Pricing**: Base OCR starts at $1.50 per 1,000 pages. Table extraction adds $15 per 1,000 pages, and Form extraction adds $50 per 1,000 pages.1  
* **Capabilities**: Provides "**Textract Queries**" for natural language extraction and Amazon Augmented AI (A2I) for human-in-the-loop review.1

**Azure AI Document Intelligence**

* **Pricing**: "Read" instance is $1.50 per 1,000 pages (discounted to $0.60 for 1M+ pages). Custom generative extraction is $30 per 1,000 pages.20  
* **Deployment**: Supports "**Connected" and "Disconnected" containers** for **high-security** environments, with annual commitment tiers starting around $10,500 for 500,000 custom extraction pages.20

### **B. High-Fidelity Specialized Services**

**LlamaParse (LlamaIndex)**

* **Pricing**: Offers **1,000 free pages per day**; paid tiers include a "**cost optimizer**" mode for scalable enterprise use.1  
* **Differentiator**: Focuses on "**semantic reconstruction**" to preserve hierarchy (headers, lists, nested tables) for RAG applications.1

**Reducto**

* **Pricing**: Usage-based pricing; optimized for **high-stakes finance/legal extraction**.1  
* **Differentiator**: Uses a **multi-pass VLM architecture** that performs **self-correction** on dense material like investor decks.1

**Mathpix**

* **Pricing**: Page limit for the Convert API is typically 20,000 per month, with custom scaling available.23  
* **Differentiator**: The industry leader in converting images of **mathematical and chemical notation (SMILES) into LaTeX** and machine-readable formats.23

### **C. Commercial Pricing and Capability Comparison**

| Provider | Pricing Model | Best For | Deployment |
| :---- | :---- | :---- | :---- |
| **Google Doc AI** | Per 1,000 pages | Global logistics/Tax | GCP Native 21 |
| **AWS Textract** | Per 1,000 pages | Mortgage/Form processing | AWS Native 1 |
| **Azure AI Doc** | Tiered/Commitment | Insurance/Retail | Hybrid/On-Prem 20 |
| **LlamaParse** | Daily free \+ Tiers | Agentic RAG | SaaS 1 |
| **Nanonets** | $0.30/page (Starter) | Accounts Payable | SaaS/On-Prem 25 |
| **Upstage** | $0.01 \- $0.15/page | Logistics/Waybills | SaaS 27 |
| **Apryse (PDFTron)** | $15k \- $500k ACV | Embedded SDKs | SDK/Server 28 |

## **Section 3: AI Models for Document Understanding**

The technological standard for document parsing in **2026 is the unified Vision-Language Model** (VLM). Unlike **classical pipelines that chain OCR with layout detection**, these models process the entire page as a visual tensor and generate structured Markdown or JSON directly.11

### **A. Vision Language Models (VLMs)**

**Granite-Docling-258M (IBM)**

* **Model ID**: ibm-granite/granite-docling-258M.31  
* **Architecture**: Built on Idefics3, using SigLIP2-base as the vision encoder and a Granite-165M language model.31  
* **Stats**: 258 million parameters; Apache 2.0 License.11  
* **Specialization**: **Optimized for "one-shot" parsing** of documents including math, code, and nested tables. It is designed to be an **ultra-compact component within Docling pipelines**.11  
* **Requirements**: Can run on standard consumer GPUs; "**untied weights" version available for VLLM deployment**.31

**PaddleOCR-VL-1.5 (Baidu)**

* **Model ID**: PaddlePaddle/PaddleOCR-VL-1.5.32  
* **Architecture**: 0.9B parameter model with a **NaViT-style dynamic resolution visual** encoder.33  
* **Performance**: Achieved a SOTA accuracy of 94.5% on **OmniDocBench v1.5**.30  
* **Specialization**: Excels in "Real-world physical distortions" (Skew, Warping, Illumination) and provides new capabilities for seal/stamp recognition.33

**Dolphin-v2 (ByteDance)**

* **Stats**: \~8K stars; ViT-based architecture.30  
* **Capabilities**: Detects 21 element categories and provides finer-grained element detection with reading order prediction.30

### **B. Specialized Component Models**

| Task | Leading Model | Context/Capability |
| :---- | :---- | :---- |
| **OCR** | Surya OCR | Supports 90+ languages; 97.7% accuracy 9 |
| **Layout** | Heron (Docling) | Faster PDF parsing; default in Docling v2.x 6 |
| **Formula** | MolScribe (MIT) | Transformer-based; converts molecular images to SMILES 35 |
| **Table** | TableFormer | Deep learning for complex merged-cell structures 9 |
| **OCR (General)** | DeepSeek-OCR-2 | 3B parameter model optimized for document text 36 |

## **Section 4: Comprehensive Format Conversion Matrix**

The conversion matrix below identifies the **primary tool for high-fidelity conversion**. "N/A" indicates conversions that are **semantically lossy or computationally nonsensical** (e.g., converting structured data into a raster image without rendering context).

| Source \\ Target | PDF | DOCX | PPTX | XLSX | HTML | JSON | CSV | Markdown | LaTeX | EPUB | Plain Text |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **PDF (Native)** | \- | Pandoc | Pandoc | Pandoc | Docling | Docling | Tabula | Docling | Mathpix | Pandoc | PyMuPDF |
| **PDF (Scanned)** | ABBYY | ABBYY | Marker | N/A | Marker | MinerU | Nanonets | MinerU | Mathpix | Marker | Surya |
| **DOCX** | Adobe | \- | Pandoc | Pandoc | Docling | MarkItDown | N/A | MarkItDown | Pandoc | Pandoc | Docling |
| **PPTX** | Adobe | Pandoc | \- | N/A | MarkItDown | MarkItDown | N/A | MarkItDown | N/A | Pandoc | MarkItDown |
| **XLSX** | Adobe | Pandoc | N/A | \- | Docling | MarkItDown | Pandas | MarkItDown | N/A | N/A | XLSX2txt |
| **HTML** | Chrome | Pandoc | N/A | N/A | \- | Docling | BeautifulSoup | Docling | Pandoc | Pandoc | HTML2Text |
| **XML** | N/A | Pandoc | N/A | N/A | Docling | XMLtodict | N/A | Pandoc | N/A | N/A | XML2txt |
| **JSON** | N/A | N/A | N/A | N/A | Docling | \- | JQ | MarkItDown | N/A | N/A | JQ |
| **CSV** | N/A | N/A | N/A | N/A | N/A | Pandas | \- | MarkItDown | N/A | N/A | Pandas |
| **Markdown** | Pandoc | Pandoc | Pandoc | Pandoc | Pandoc | MarkItDown | N/A | \- | Pandoc | Pandoc | MD2txt |
| **LaTeX** | TeXLive | Pandoc | N/A | N/A | Pandoc | N/A | N/A | Docling | \- | Pandoc | Detex |
| **EPUB** | Calibre | Pandoc | N/A | N/A | Pandoc | N/A | N/A | MarkItDown | N/A | \- | Epub2txt |
| **RTF** | Adobe | Word | N/A | N/A | Pandoc | MarkItDown | N/A | MarkItDown | N/A | N/A | RTF2txt |
| **ODT** | Pandoc | Word | N/A | N/A | Pandoc | N/A | N/A | Pandoc | N/A | Pandoc | ODT2txt |
| **PNG/JPG** | Marker | N/A | N/A | N/A | Marker | Upstage | Nanonets | Marker | MolScribe | N/A | Tesseract |
| **SVG** | Inkscape | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

*Note: Conversions like JSON to PDF are marked N/A as they typically require a custom templating engine (e.g., Jinja2 \+ WeasyPrint) rather than a direct format converter.*

## **Section 5: Benchmarks and Quantitative Comparisons**

Evaluation in 2026 relies on the **OmniDocBench v1.5** framework, which measures a model's ability to jointly assess text, formulas, tables, and reading order.36

### **A. PDF to Markdown Accuracy (OmniDocBench v1.5)**

The metrics are calculated as: ![][image1].36

| System/Model | Overall Score | Text Accuracy | Table (TEDS) | Formula (CDM) |
| :---- | :---- | :---- | :---- | :---- |
| **PaddleOCR-VL-1.5** | 94.5% | 98.1% | 91.2% | 94.2% 30 |
| **Gemini 3 Pro** | 93.4% | 97.9% | 89.5% | 92.8% 30 |
| **Dolphin-v2** | 89.8% | 95.4% | 85.1% | 88.9% 30 |
| **Docling (Granite)** | 88.9% | 94.6% | 84.8% | 87.3% 11 |
| **olmOCR (Allen AI)** | 83.9% | 91.5% | 79.2% | 81.0% 30 |

### **B. Throughput (Pages Per Second)**

Throughput benchmarked on NVIDIA H100 GPU (unless specified).

| Tool | Speed (pps) | Hardware | Context |
| :---- | :---- | :---- | :---- |
| **Marker (Batch)** | 25.0 | H100 | High-fidelity neural 38 |
| **PyMuPDF4LLM** | 120.0 | CPU (vCPU x16) | Native text only 18 |
| **Docling (v2)** | 8.5 | A6000 | Heron layout model 6 |
| **MinerU (Hybrid)** | 5.2 | A6000 | High-precision scientific 2 |
| **Tesseract** | 1.8 | CPU | Classical OCR 39 |

### **C. Cost Analysis ($ per 1 Million Pages)**

Analysis compares managed API costs against estimated compute for self-hosted instances on AWS g5.2xlarge.

| Provider/Strategy | Managed Cost | Self-Hosted GPU | Rationale |
| :---- | :---- | :---- | :---- |
| **Azure Read** | $600 | N/A | High-volume commitment 20 |
| **Docling (Granite)** | N/A | $210 | 1M pages @ 8pps 6 |
| **Marker (API)** | $150 | N/A | 1/4th cloud competitor price 34 |
| **Google Custom Ext** | $20,000 | N/A | 1M pages @ $20/k 19 |

## **Section 6: RAG and LLM Integration Ecosystem**

The **integration of document parsers into RAG pipelines** in 2026 is dominated by "**semantic chunkers**" that leverage the **structural metadata (DocTags)** produced during conversion.10

### **A. Framework Integration Classes**

* **LlamaIndex**: Uses DoclingReader (JSON mode) to extract bounding box information for multimodal grounding. LlamaParse is the native agentic parser for the LlamaIndex ecosystem.1  
* **LangChain**: Features DoclingLoader with support for DOC\_CHUNKS export, allowing documents to be split by structural boundaries (headings) during the load phase.40  
* **Haystack**: Integrates **DoclingConverter and UnstructuredFileConverter** for **multi-pass ETL pipelines**.41

### **B. Comparison of Chunking Approaches**

| Chunking Strategy | Preserves Hierarchy | Contextual Metadata | Computational Cost |
| :---- | :---- | :---- | :---- |
| **Fixed-Size** | No | None | Low |
| **Semantic (Embedding)** | Partial | Local context | Moderate |
| **Structure-Aware** | Yes (Headings) | Section hierarchy | Low (Heuristic) |
| **Hybrid (Docling/VLM)** | Absolute | Page, Bbox, DocTags | Moderate (Neural) 10 |

## **Section 7: Production Deployment Patterns**

Productionizing document conversion in 2026 requires handling **massive asynchronous** workloads and **strict security** boundaries.

### **A. Containerization and Orchestration**

* **Docker Images**: Official images for **Docling, MinerU, and Unstructured** are provided.6 MinerU images are **optimized for multiple architectures**, including domestic platforms like **Ascend and Kunlunxin**.2  
* **Kubernetes**: Scaling is typically handled via horizontal pod autoscalers (HPA) using custom metrics from model serving frameworks like VLLM or Docling-serve.6  
* **Batch Processing**: Hancom OpenDataLoader v2.0 is optimized for massive local batch jobs, processing up to 1 million documents without external API calls to maintain security.3

### **B. Quality Assurance and Monitoring**

* **Confidence Scoring**: Tools like **Azure Document Intelligence** and **Reducto** provide per-word or per-block confidence scores.1  
* **HITL (Human-in-the-Loop)**: **AWS Textract's A2I** service allows developers to set **thresholds** (e.g., if confidence \< 80%, route to human review).1  
* **Observability**: Most production pipelines integrate **Scarf for usage analytics** (which is now opt-out by default in **Unstructured v0.22+)** and standard **Prometheus/Grafana stacks for GPU temperature and inference latency**.16

***\[ SEE Note: SCARF and OSS Competitors \]***

## **Section 8: Edge Cases and Specialist Capabilities**

As document parsing matures, the "**long tail" of document variety** represents the current frontier.

### **A. Scientific, Chemical, and Musical Notation**

* **Mathematical Notation**: **Mathpix** remains the benchmark for complex LaTeX reconstruction. Marker and MinerU convert "most" equations but often struggle with **nested fractions or non-standard symbols**.2  
* **Chemical Formulas**: **MolScribe (MIT) and OSRA (National Cancer Institute)** are the primary open-source tools for converting molecular images into **SMILES strings**.35  
* **Musical Notation**: **Soundslice and OpenOMR** provide **OMR (Optical Music Recognition)** for converting printed **sheet music into MusicXML or MIDI**.44

***\[ SEE NOTE: OMR to MusicXML \]***

***\[ SEE NOTE: Music Notation \]***

### **B. Script and Language Challenges**

* **RTL (Arabic/Hebrew)**: AWS Textract and Surya OCR provide specific optimizations for **right-to-left scripts**, preventing the common "flipped text" errors found in older Tesseract versions.1  
* **Vertical CJK**: PaddleOCR-VL-1.5 is the current leader in **vertical Chinese/Japanese/Korean** text recognition, especially in **stylized or warped** documents.33  
* **Handwriting**: **ICR (Intelligent Character Recognition**) in the Spring 2026 release of **Apryse and Microsoft's specialized neural models** handle messy handwritten notes on complex backgrounds.37

***\[ SEE NOTE: Mobile HTR \]***

### **C. Security and Protection**

* **Encrypted/Password PDF**: PyMuPDF and Apryse support **password-based decryption** for programmatic access.18  
* **Sanitization**: Apryse Spring 2026 introduced a "**PDF Sanitization API**" to scrub sensitive metadata and revision history before sharing.46  
* **DRM (EPUB)**: While conversion tools like MarkItDown support EPUB, they generally fail on **DRM-protected files** unless the proper decryption keys are provided at runtime.7

## **Section 9: Emerging Standards and Future Directions**

The focus of the **document ecosystem** is moving toward **universal accessibility** and **machine-verifiable compliance**.

* **PDF 2.0 and PDF/UA-2**: Published in 2024 and gaining tool support in 2026, **PDF/UA-2** (Universal Accessibility) addresses the shortcomings of UA-1 by incorporating **MathML** support. The **LaTeX** project now natively supports PDF/UA-2 for scientific papers.47  
* **Auto-Tagging**: **Apryse and Hancom** are leading the push for "**AI-generated accessibility tagging**," allowing non-compliant legacy documents to be automatically updated for screen-reader compatibility.4  
* **OOXML Strict**: The industry is largely moving toward **OOXML Strict (ISO/IEC 29500\)** over Transitional modes to ensure **long-term archival stability**, with Pandoc v3.9+ providing the most robust handling of these variants.  
* **W3C Web Annotation**: Modern parsers like Docling are exploring the export of metadata in the **Web Annotation Data Model** to facilitate cross-platform **collaborative review** of AI-extracted data.

## **Section 10: Recommended Architecture for a Unified Conversion System**

A robust "Doc Shape-Shifter" system in 2026 must be **modular, security-conscious, and content-aware**.

### **A. System Architecture**

The proposed system follows a "**Router-Worker**" pattern:

1. **Gateway**: FastAPI service accepting files.  
2. **MIME Inspector**: Uses **Magika** to determine the "true" format regardless of extension.5  
3. **Router**: Determines the backend based on a hierarchy:  
   * *Scientific/Math*: Route to **MinerU** or **Mathpix**.2  
   * *High-Stakes Legal/Finance*: Route to **Reducto** or **Docling**.1  
   * *General Batch*: Route to **Marker** for speed.38  
   * *Sensitive On-Prem*: Route to **Hancom OpenDataLoader**.3  
4. **Transformation Worker**: Executes the tool in a stateless container.  
5. **Quality Checker**: Uses Granite-Docling to score the output.11 If score \< 0.85, it triggers a "Refiner" pass using a high-parameter VLM (Gemini 3).

### **B. Project Skeleton: pyproject.toml**

Ini, TOML

\[project\]  
name \= "doc-shape-shifter"  
version \= "2026.03.29"  
dependencies \= \[  
    "docling\>=2.82.0",  
    "markitdown\>=0.1.5",  
    "mineru\[all\]\>=2.7.6",  
    "marker-pdf\>=0.3.3",  
    "magika\>=0.5.1"  
\]

\[tool.uv\]  
managed \= true  
package \= true

### **C. Development Effort Estimates**

| Component | Logic | Effort (Person-Weeks) |
| :---- | :---- | :---- |
| **Routing Logic** | Content-aware decision trees | 3 |
| **Model Serving** | GPU-accelerated VLLM/Docling-serve | 6 |
| **Validation Loop** | Confidence-based fallback chains | 4 |
| **Security Layer** | PDF sanitization and DRM handling | 3 |
| **Total** |  | **16 Weeks** |

This survey demonstrates that while the core challenge of "reading" a document is largely solved by state-of-the-art VLMs like PaddleOCR-VL-1.5, the engineering focus has shifted toward high-speed orchestration, accessibility compliance (PDF/UA-2), and the seamless integration of structural document data into autonomous agent workflows.

#### **Works cited**

1. Top Document Parsing APIs for 2026 | LlamaIndex, accessed March 29, 2026, [https://www.llamaindex.ai/insights/top-document-parsing-apis](https://www.llamaindex.ai/insights/top-document-parsing-apis)  
2. GitHub \- opendatalab/MinerU: Transforms complex documents like PDFs into LLM-ready markdown/JSON for your Agentic workflows., accessed March 29, 2026, [https://github.com/opendatalab/mineru](https://github.com/opendatalab/mineru)  
3. Hancom OpenDataLoader PDF v2.0 tops GitHub trending overall, accessed March 29, 2026, [https://www.digitaltoday.co.kr/en/view/42311/hancom-opendataloader-pdf-v2-0-tops-github-trending-overall](https://www.digitaltoday.co.kr/en/view/42311/hancom-opendataloader-pdf-v2-0-tops-github-trending-overall)  
4. Hancom Tops Open-Source PDF Benchmarks with OpenDataLoader PDF v2.0, accessed March 29, 2026, [https://enmobile.prnasia.com/releases/global/hancom-tops-open-source-pdf-benchmarks-with-opendataloader-pdf-v2-0-525226.shtml](https://enmobile.prnasia.com/releases/global/hancom-tops-open-source-pdf-benchmarks-with-opendataloader-pdf-v2-0-525226.shtml)  
5. Releases · microsoft/markitdown \- GitHub, accessed March 29, 2026, [https://github.com/microsoft/markitdown/releases](https://github.com/microsoft/markitdown/releases)  
6. GitHub \- docling-project/docling: Get your documents ready for gen AI, accessed March 29, 2026, [https://github.com/docling-project/docling](https://github.com/docling-project/docling)  
7. microsoft/markitdown: Python tool for converting files and ... \- GitHub, accessed March 29, 2026, [https://github.com/microsoft/markitdown](https://github.com/microsoft/markitdown)  
8. Best Open Source PDF to Markdown Tools (2026): Marker vs MinerU vs MarkItDown, accessed March 29, 2026, [https://jimmysong.io/blog/pdf-to-markdown-open-source-deep-dive/](https://jimmysong.io/blog/pdf-to-markdown-open-source-deep-dive/)  
9. From PDFs to Markdown \- DEV Community, accessed March 29, 2026, [https://dev.to/ashokan/from-pdfs-to-markdown-evaluating-document-parsers-for-air-gapped-rag-systems-58eh](https://dev.to/ashokan/from-pdfs-to-markdown-evaluating-document-parsers-for-air-gapped-rag-systems-58eh)  
10. RAG with LlamaIndex \- Docling, accessed March 29, 2026, [https://docling-project.github.io/docling/examples/rag\_llamaindex/](https://docling-project.github.io/docling/examples/rag_llamaindex/)  
11. IBM Granite-Docling: End-to-end document understanding, accessed March 29, 2026, [https://www.ibm.com/new/announcements/granite-docling-end-to-end-document-conversion](https://www.ibm.com/new/announcements/granite-docling-end-to-end-document-conversion)  
12. Hancom's Open Data Loader PDF v2.0 Tops GitHub Trending \- Seoul Economic Daily, accessed March 29, 2026, [https://en.sedaily.com/news/2026/03/23/hancoms-open-data-loader-pdf-v20-tops-github-trending](https://en.sedaily.com/news/2026/03/23/hancoms-open-data-loader-pdf-v20-tops-github-trending)  
13. OpenDataLoader PDF v2.0 Hits \#1 on GitHub Trending Globally: Just One Week After Launch \- Medium, accessed March 29, 2026, [https://medium.com/codetodeploy/opendataloader-pdf-v2-0-hits-1-on-github-trending-globally-just-one-week-after-launch-a675237d9425](https://medium.com/codetodeploy/opendataloader-pdf-v2-0-hits-1-on-github-trending-globally-just-one-week-after-launch-a675237d9425)  
14. Releases · Unstructured-IO/unstructured \- GitHub, accessed March 29, 2026, [https://github.com/unstructured-io/unstructured/releases](https://github.com/unstructured-io/unstructured/releases)  
15. Convert documents to structured data effortlessly. Unstructured is open-source ETL solution for transforming complex documents into clean, structured formats for language models. Visit our website to learn more about our enterprise grade Platform product for production grade workflows, partitioning, enrichments, chunking and embedding. · GitHub, accessed March 29, 2026, [https://github.com/Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured)  
16. unstructured/CHANGELOG.md at main \- GitHub, accessed March 29, 2026, [https://github.com/Unstructured-IO/unstructured/blob/main/CHANGELOG.md](https://github.com/Unstructured-IO/unstructured/blob/main/CHANGELOG.md)  
17. marker-pdf 0.3.3 \- PyPI, accessed March 29, 2026, [https://pypi.org/project/marker-pdf/0.3.3/](https://pypi.org/project/marker-pdf/0.3.3/)  
18. pymupdf/pymupdf4llm \- GitHub, accessed March 29, 2026, [https://github.com/pymupdf/pymupdf4llm](https://github.com/pymupdf/pymupdf4llm)  
19. Document AI pricing \- Google Cloud, accessed March 29, 2026, [https://cloud.google.com/document-ai/pricing](https://cloud.google.com/document-ai/pricing)  
20. Azure Document Intelligence in Foundry Tools pricing, accessed March 29, 2026, [https://azure.microsoft.com/en-us/pricing/details/document-intelligence/](https://azure.microsoft.com/en-us/pricing/details/document-intelligence/)  
21. Best Document Extraction APIs (2026), accessed March 29, 2026, [https://www.lido.app/blog/best-document-extraction-apis](https://www.lido.app/blog/best-document-extraction-apis)  
22. Limits | Document AI \- Google Cloud Documentation, accessed March 29, 2026, [https://docs.cloud.google.com/document-ai/limits](https://docs.cloud.google.com/document-ai/limits)  
23. Convert API User Guide: Rate and page limits \- Mathpix, accessed March 29, 2026, [https://mathpix.com/docs/convert/limits](https://mathpix.com/docs/convert/limits)  
24. Convert handwritten chemical diagrams to SMILES code \- YouTube, accessed March 29, 2026, [https://www.youtube.com/watch?v=830Z4bU6rY4](https://www.youtube.com/watch?v=830Z4bU6rY4)  
25. Nanonets Pricing 2026 \- TrustRadius, accessed March 29, 2026, [https://www.trustradius.com/products/nanonets/pricing](https://www.trustradius.com/products/nanonets/pricing)  
26. Nanonets Pricing 2026, accessed March 29, 2026, [https://www.g2.com/products/nanonets/pricing](https://www.g2.com/products/nanonets/pricing)  
27. Pricing \- Upstage AI, accessed March 29, 2026, [https://www.upstage.ai/pricing/api](https://www.upstage.ai/pricing/api)  
28. Apryse Software Pricing & Plans 2026: See Your Cost \- Vendr, accessed March 29, 2026, [https://www.vendr.com/marketplace/apryse](https://www.vendr.com/marketplace/apryse)  
29. Apryse Pricing and Licensing, accessed March 29, 2026, [https://apryse.com/pricing](https://apryse.com/pricing)  
30. OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations \- ResearchGate, accessed March 29, 2026, [https://www.researchgate.net/publication/394650843\_OmniDocBench\_Benchmarking\_Diverse\_PDF\_Document\_Parsing\_with\_Comprehensive\_Annotations](https://www.researchgate.net/publication/394650843_OmniDocBench_Benchmarking_Diverse_PDF_Document_Parsing_with_Comprehensive_Annotations)  
31. ibm-granite/granite-docling-258M \- Hugging Face, accessed March 29, 2026, [https://huggingface.co/ibm-granite/granite-docling-258M](https://huggingface.co/ibm-granite/granite-docling-258M)  
32. PaddleOCR-VL-1.5 (Better Than DeepSeek OCR 2\) : Best Open-Source OCR Model Just Dropped \- YouTube, accessed March 29, 2026, [https://www.youtube.com/watch?v=sOtiHrlzE68](https://www.youtube.com/watch?v=sOtiHrlzE68)  
33. PaddleOCR-VL Usage Tutorial, accessed March 29, 2026, [https://www.paddleocr.ai/latest/en/version3.x/pipeline\_usage/PaddleOCR-VL.html](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html)  
34. swswsws583/marker-solo: Convert PDF to markdown quickly with high accuracy \- GitHub, accessed March 29, 2026, [https://github.com/swswsws583/marker-solo](https://github.com/swswsws583/marker-solo)  
35. Top Chemical OCR Tools: From Image Recognition to Structure Reconstruction \- FreeChemDraw, accessed March 29, 2026, [https://freechemdraw.com/en/chemical-structure-knowledge-base/top-chemical-OCR-tools/](https://freechemdraw.com/en/chemical-structure-knowledge-base/top-chemical-OCR-tools/)  
36. opendatalab/OmniDocBench: \[CVPR 2025\] A ... \- GitHub, accessed March 29, 2026, [https://github.com/opendatalab/OmniDocBench](https://github.com/opendatalab/OmniDocBench)  
37. OmniDocBench v1.5 Benchmark \- Emergent Mind, accessed March 29, 2026, [https://www.emergentmind.com/topics/omnidocbench-v1-5](https://www.emergentmind.com/topics/omnidocbench-v1-5)  
38. GitHub \- datalab-to/marker: Convert PDF to markdown \+ JSON quickly with high accuracy, accessed March 29, 2026, [https://github.com/datalab-to/marker](https://github.com/datalab-to/marker)  
39. 10 Open Source OCR Tools You Should Know About \- Koncile, accessed March 29, 2026, [https://www.koncile.ai/en/ressources/10-open-source-ocr-tools-you-should-know-about](https://www.koncile.ai/en/ressources/10-open-source-ocr-tools-you-should-know-about)  
40. Docling integration \- Docs by LangChain, accessed March 29, 2026, [https://docs.langchain.com/oss/python/integrations/document\_loaders/docling](https://docs.langchain.com/oss/python/integrations/document_loaders/docling)  
41. UnstructuredFileConverter \- Haystack Documentation \- deepset AI, accessed March 29, 2026, [https://docs.haystack.deepset.ai/docs/unstructuredfileconverter](https://docs.haystack.deepset.ai/docs/unstructuredfileconverter)  
42. Docling | Haystack, accessed March 29, 2026, [https://haystack.deepset.ai/integrations/docling](https://haystack.deepset.ai/integrations/docling)  
43. Base price per unit \- Nanonets Overview, accessed March 29, 2026, [https://docs.nanonets.com/docs/base-price-per-unit](https://docs.nanonets.com/docs/base-price-per-unit)  
44. OpenOMR download | SourceForge.net, accessed March 29, 2026, [https://sourceforge.net/projects/openomr/](https://sourceforge.net/projects/openomr/)  
45. The 8 Most Underrated Notation Software Tools 2026 | soundnotation.com, accessed March 29, 2026, [https://soundnotation.com/en/music-technology/underrated-notation-software-2026/](https://soundnotation.com/en/music-technology/underrated-notation-software-2026/)  
46. Spring 2026 Release Preview \- Apryse, accessed March 29, 2026, [https://apryse.com/releases/spring-2026-early-look](https://apryse.com/releases/spring-2026-early-look)  
47. What PDF 2.0 Means for Accessibility | by PDF4WCAG | Data And Beyond | Medium, accessed March 29, 2026, [https://medium.com/data-and-beyond/what-pdf-2-0-means-for-accessibility-6588f74492ac](https://medium.com/data-and-beyond/what-pdf-2-0-means-for-accessibility-6588f74492ac)  
48. Auto-tagging for PDF/UA – Improving Accessibility for all using the Apryse SDK, accessed March 29, 2026, [https://apryse.com/blog/auto-tagging-pdf-ua-compliance](https://apryse.com/blog/auto-tagging-pdf-ua-compliance)

[image1]: <data:image/png;base64,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>