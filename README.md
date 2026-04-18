# Vision and NLP Photo Search Engine

## Overview
This is a fully serverless web application that allows users to upload photos and search through them using natural language queries. 

Rather than relying on generic buzzwords, this project specifically leverages Computer Vision to automatically extract visual features from uploaded images, and Natural Language Processing (NLP) to parse conversational search queries (e.g., "Show me dogs and cats" or "Find pictures of the ocean"). 

## Architecture and Core Components
This project follows an event-driven serverless architecture on AWS:

* Frontend Hosting: Amazon S3 (B1) configured for static website hosting.
* Photo Storage: Amazon S3 (B2) for storing the actual image files.
* Computer Vision: Amazon Rekognition to automatically detect labels/objects in uploaded photos.
* Natural Language Processing: Amazon Lex to parse search queries and identify key search terms.
* Search Engine: Amazon OpenSearch (ElasticSearch) to store photo metadata and execute fast text searches.
* Compute: AWS Lambda to run the backend business logic without managing servers:
  * LF1 (index-photos): Triggered by S3 uploads to extract custom metadata, call Rekognition, and index the data in OpenSearch.
  * LF2 (search-photos): Triggered by API Gateway to pass user queries to Lex and fetch matching images from OpenSearch.
* API Routing: Amazon API Gateway to expose REST endpoints (PUT /photos and GET /search) to the frontend.
* Infrastructure as Code (IaC): AWS CloudFormation (SAM) to provision all resources.
* CI/CD: AWS CodePipeline to automatically build and deploy code upon GitHub commits.

## How It Works

1. Upload Pipeline: A user uploads a photo to the S3 bucket (B2). This triggers Lambda LF1, which sends the image to Rekognition to extract labels. LF1 combines these extracted labels with any custom user labels and stores them as a JSON document in OpenSearch.
2. Search Pipeline: A user types a search query in the frontend UI. The request goes through API Gateway to Lambda LF2. LF2 sends the natural language string to Amazon Lex, which extracts the core keywords. LF2 then queries OpenSearch using those keywords and returns the matching S3 image URLs to the frontend.

## Tech Stack
* Cloud Provider: Amazon Web Services (AWS)
* Backend: Python 3.12 (boto3)
* Frontend: HTML, CSS, JavaScript
* DevOps: GitHub, AWS CodePipeline, AWS CloudFormation

## Course Information
Course: Cloud Computing and Big Data Systems (Spring 2026)