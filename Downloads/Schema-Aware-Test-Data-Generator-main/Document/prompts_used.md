# 💬 Project Development Prompts Log

This document records the actual prompts and instructions provided by the user during the development of the **AI-Powered Schema-Aware Test Data Generator** project. These prompts reflect the evolutionary journey of building, testing, restructuring, and deploying the application.

---


## 🚀 Phase 1: Integrating Schema-Aware Generator Prototype

### Prompt 1
> **Timestamp:** `2026-06-09T05:28:03Z`

```text
<USER_REQUEST>
You are a senior full-stack AI product engineer.

I am building an AI prototype project titled:

"Schema-Aware Test Data Generator"

My goal is to integrate my existing backend with a professional frontend UI. 
I already have backend logic and I also have a reference UI from a video/code file. 
You must carefully inspect the entire project before modifying anything.

IMPORTANT RULES:
1. Do not remove, rewrite, or break any existing backend logic.
2. Do not delete any API route, function, model, validation logic, file upload logic, database logic, schema parsing logic, or AI generation logic.
3. If the frontend UI has missing buttons or missing pages for existing backend features, create those frontend elements.
4. If the backend has features but the frontend does not expose them, add proper UI components for them.
5. If the frontend has buttons but backend APIs are missing, create clean backend routes for them without disturbing existing code.
<truncated 8031 bytes>
```

---

### Prompt 2
> **Timestamp:** `2026-06-09T06:49:22Z`

```text
bro i could not able to upload the files if i click the upload the file i couldnot upload it only depends Paste SQL schema , it asking provide shema for that
```

---


## 🚀 Phase 2: Restructuring Project for GitHub - Part 1

### Prompt 3
> **Timestamp:** `2026-06-09T07:45:20Z`

```text
@[../../../.gemini/antigravity/brain/78e66cd5-f074-44aa-9250-80e5972d9eb3/github_restructure_plan.md.resolved]
do this plan accordingly to this file
```

---


## 🚀 Phase 3: Restructuring Project for GitHub - Part 2

### Prompt 4
> **Timestamp:** `2026-06-09T07:52:58Z`

```text
@[../../../.gemini/antigravity/brain/78e66cd5-f074-44aa-9250-80e5972d9eb3/github_restructure_plan.md.resolved]
scan this file and do that plan properl.
remove unwanted file or just put the unwanted in one folder name as delete.
i attached the file structure so do accordinly
```

---


## 🚀 Phase 4: Collaborating on GitHub Repository Setup

### Prompt 5
> **Timestamp:** `2026-06-09T08:45:21Z`

```text
now all the code was done. now there was a prblm we have team of 4 . and we have to upload it into the github , but it shows like 4 members contribution . so give me the proper guide to create repo and how to connect with all other team mates. and also seperate the files for my team mates.
1st piority for me 
2nd and 3rd are equal and 4th is lest.
seperate the files for each person by piority . and tell me how to implemet and put it in github.
```

---

### Prompt 6
> **Timestamp:** `2026-06-09T08:59:54Z`

```text
bro they all accept my invite after that what i do . can you tell me more clear
```

---

### Prompt 7
> **Timestamp:** `2026-06-09T09:04:47Z`

```text
extract the username and the repo name also. give me the commands for all my team mates to upload this.
```

---

### Prompt 8
> **Timestamp:** `2026-06-09T09:07:46Z`

```text
bro its making error
```

---

### Prompt 9
> **Timestamp:** `2026-06-09T09:45:33Z`

```text
bro after they push is there anything i do like pull request and tell me where the link was after i upload the link if i change anything it will refect the link also right. like if any bug was in my code i was able to chang it right . and also my team mate can upload the repo after i submit the link it still change able rigt
```

---

### Prompt 10
> **Timestamp:** `2026-06-09T09:46:40Z`

```text
bro my frnds was still uploading but my sir asling the link . so can i share the link .
```

---

### Prompt 11
> **Timestamp:** `2026-06-09T09:53:54Z`

```text
bro after the creating the clone my team mate two didnt know where  to copy the frontend file
```

---

### Prompt 12
> **Timestamp:** `2026-06-09T10:15:10Z`

```text
team 3 error
```

---


## 🚀 Phase 5: Preparing Schema Data Presentation

### Prompt 13
> **Timestamp:** `2026-06-12T12:52:45Z`

```text
<USER_REQUEST>
I have a mock presentation today for my project titled:

“Schema-Aware Test Data Generator”

Act like a senior software engineer, project guide, and placement interviewer.

Explain each and every single thing about this project in a very simple and professional way so that I can confidently present it in front of faculty/interviewers.

Project idea:
The project is a Schema-Aware Test Data Generator. It takes database schema or table structure as input and generates realistic test data automatically based on column names, data types, constraints, relationships, and rules. The goal is to help developers, testers, and QA teams quickly create valid dummy/test data for databases, APIs, and applications.

Explain the project in the following format:

1. Project Introduction
- What is this project?
- Why is this project needed?
- What problem does it solve?
- Who will use this project?

2. Real-world Problem
Explain why test data generation is difficult manually.
Mention problems like:
<truncated 7302 bytes>
```

---


## 🚀 Phase 6: Upgrading Schema Generator & Integrating Groq API

### Prompt 14
> **Timestamp:** `2026-06-13T15:07:00Z`

```text
<USER_REQUEST>
You are a senior full-stack AI engineer. Upgrade my existing project titled **“Schema-Aware Test Data Generator”** into an AI-powered prototype suitable for a placement technical round.

My old project currently works like this:

* User provides input schema.
* The system parses the schema.
* Faker generates test data directly based on the schema.
* The generated data is validated and exported.

Now I want to upgrade it into a smarter AI-integrated product.

Project title:
**AI-Powered Schema-Aware Test Data Generator**

Existing tech stack:
Frontend:

* React
* TypeScript
* Vite
* Tailwind CSS
* shadcn/ui
* Zustand
* TanStack Router

Backend:

* Python
* FastAPI
* Uvicorn
* Faker
* Pandas
* Pytest
* httpx
* python-multipart

Existing backend modules:

* `api.py`
* `ddl_parser.py`
* `schema_models.py`
* `dependency_resolver.py`
* `data_generator.py`
* `validators.py`
* `exporters.py`
* `agent.py`
* `utils.py`

Do not remove the existing working features. Upgrade the project cleanly.

<truncated 12795 bytes>
```

---

### Prompt 15
> **Timestamp:** `2026-06-13T15:40:27Z`

```text
i am  going to use my groq api key . you already know mine so can ypu integrate them and put it in gitigonre file
```

---

### Prompt 16
> **Timestamp:** `2026-06-13T15:42:49Z`

```text
this is my 
groq : [REDACTED_GSK_KEY_1]

you can also check it in csc_project. and also change the readme file for this
```

---

### Prompt 17
> **Timestamp:** `2026-06-13T16:01:39Z`

```text
new groq api key
[REDACTED_GSK_KEY_2]
```

---

### Prompt 18
> **Timestamp:** `2026-06-13T16:11:50Z`

```text
now run the code
```

---

### Prompt 19
> **Timestamp:** `2026-06-13T16:26:22Z`

```text
<USER_REQUEST>
even though i choose any template for this, it only give the test case for the given schema it does not generate any shema based on the user template.
<truncated 2334 bytes>
```

---


## 🚀 Phase 7: Running The Project Locally

### Prompt 20
> **Timestamp:** `2026-06-13T17:01:43Z`

```text
how to run this code
```

---


## 🚀 Phase 8: Running & Troubleshooting Setup

### Prompt 21
> **Timestamp:** `2026-06-14T04:46:15Z`

```text
run the code
```

---

### Prompt 22
> **Timestamp:** `2026-06-14T04:54:38Z`

```text
bro this causes error. it does not generating the schema
```

---

### Prompt 23
> **Timestamp:** `2026-06-14T05:03:03Z`

```text
run the code now
```

---

### Prompt 24
> **Timestamp:** `2026-06-14T05:06:00Z`

```text
till now passing the error. please check the error and test the program
```

---


## 🚀 Phase 9: Fixing LLM API Connection & Ollama Cleanup

### Prompt 25
> **Timestamp:** `2026-06-14T05:48:12Z`

```text
bro still now my api key does not work or connected with my project. because we using multiplre thing like olama remove that unwanted things . use proper api key  and please make it run with llm.
```

---

### Prompt 26
> **Timestamp:** `2026-06-14T08:30:07Z`

```text
bro its all completely working thankyou so much. and aslo i have to push the modified files to github . so can you chamge the readme file and files to push it in the github. first arrange files which are going to psuh in github and change the readme file with proper clear explaination even the non technical person can understood. after that ask me before pushing the files to github
```

---


## 🚀 Phase 10: Final Deployment & Git Consolidation

### Prompt 27
> **Timestamp:** `2026-06-14T08:46:46Z`

```text
before that if i push it, it will show i done the entire part it shows ghe my team mate also done before pushing this. just clarify it
```

---

### Prompt 28
> **Timestamp:** `2026-06-14T08:51:01Z`

```text
push the edited file to the repo. you already scanned the files right. push it
```

---

### Prompt 29
> **Timestamp:** `2026-06-14T09:11:00Z`

```text
remove the team and sample_data/input - because we already have the sample data in the project itself so remove it and also remove the demo_script in the documentation and put all the prompts i given to you for this project.literlly i send hours to you for this project so put the promts
```

---

