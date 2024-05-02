## Gemabry (Google AI Hackathon)

Welcome to my project submission for the [Google AI Hackathon](https://googleai.devpost.com/)! 👋

![image](https://github.com/junxianyong/Gemabry/assets/21261586/664e62ba-1a95-4486-832c-69d52880827c)

Gemabry is a collaborative platform prototype aimed at enabling users to engage dynamically with AI. Users can submit and share AI prompts, explore a curated collection, and learn to craft effective prompts to unlock AI's potential.

### Key Features
-   **Submit and Share AI Prompts:** Contribute to a growing database of diverse prompts.
-   **Play and Experiment:** Test different AI models from a collection of community-curated prompt.
-   **Learn and Grow:** Enhance your understanding of AI capabilities and prompt crafting.

### Getting Started
#### Prerequisites
Ensure you have Python 3.8 or higher installed on your system and an API Key from [Google AI Studio](https://ai.google.dev/).

#### Install Requirements
`pip install -r requirements.txt` 

#### API Key Configuration
1.  Modify the `.env` file in the root directory of the cloned repository.
2.  Replace `YOUR_API_KEY` on the following line with your own API Key:
    `API_KEY=YOUR_API_KEY` 
    
#### Running the Application
Start exploring Gemabry by running:
`python app.py` 

### Usage
After starting the application, you can log in using the following test account to start exploring:
-   **Username:** `test@test.com`
-   **Password:** `123`

### Checking of Available Models
You can use `check_available_models.py` to check the models available under the API Key that you have created. Gemabry has the implementation for the following models:
 - `gemini-pro`
 - `gemini-pro-vision`
 - `gemini-1.5-pro-latest`

### Disclaimer
This software is a prototype developed for the Google AI Hackathon and is not intended for production use. It is recommended for local testing and development only. The platform has not been extensively tested for security vulnerabilities and should be used accordingly. 😊
