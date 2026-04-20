import os
import re
import requests
import textwrap
from io import BytesIO
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# 1. INITIALIZATION
load_dotenv()
app = FastAPI(title="KantoWit: The Recursive AI Architect")

# Setup local storage
os.makedirs("output_images", exist_ok=True)
app.mount("/images", StaticFiles(directory="output_images"), name="images")

# API Clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI") 

client = OpenAI(api_key=OPENAI_API_KEY)
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.kantowit_db
captions_collection = db.witty_captions

# 2. SCHEMAS
class OptionRequest(BaseModel):
    subject: str
    audience_profile: List[str] = Field(default_factory=lambda: ["General Audience"])
    visual_theme: str = "anime chibi"

class FinalizeRequest(BaseModel):
    image_url: str
    caption: str
    subject: str

# 3. CORE UTILITIES
def overlay_text_on_image(image_url: str, text: str, output_filename: str):
    """Selyadong Step 3: Professional Sticker Assembly"""
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(img)
    width, height = img.size

    try:
        # Siguraduhin na nása folder ang font file na ito
        font = ImageFont.truetype("Arial Bold.ttf", 45)
    except:
        font = ImageFont.load_default()

    display_text = text.upper()
    wrapped_text = textwrap.fill(display_text, width=10)
    
    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    x = (width - w) / 2
    y = height - h - 150 
    
    padding_h, padding_v = 40, 20
    draw.rounded_rectangle(
        [x - padding_h, y - padding_v, x + w + padding_h, y + h + padding_v],
        radius=25,
        fill=(255, 255, 255, 245),
        outline=(0, 0, 0),
        width=5
    )
    
    draw.multiline_text((x, y), wrapped_text, font=font, fill="black", align="center")

    output_path = os.path.join("output_images", output_filename)
    img.save(output_path)
    return output_filename

# Selyadong Bug Fix para sa overlay_dual_text_on_image function
def overlay_dual_text_on_image(image_url, subject, caption, output_filename):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # 1. SETUP FONT Logic (Flexibility is Key)
    # Start with a bold font, we will scale it down if needed
    try:
        # Siguraduhin na nása system mo ang font na ito o palitan ng path sa .ttf
        font_main = ImageFont.truetype("Arial Bold.ttf", 35) 
        font_sub = ImageFont.truetype("Arial.ttf", 40)
    except:
        font_main = font_sub = ImageFont.load_default()

    # --- 2. THE BUG FIX: FONT SCALING Logic for Subject ---
    # Ito ang selyadong Principal move para hindi sobrang laki
    def get_flexible_font(draw, text, font, max_width):
        current_size = font.size
        while draw.textbbox((0, 0), text, font=font)[2] > max_width:
            current_size -= 5
            font = ImageFont.truetype(font.path, current_size)
            if current_size <= 20: # Minimum readable size
                break
        return font

    # --- 3. OVERLAY CAPTION (Top) ---
    # Example witty caption from GPT-4o: "Selyadong Sana All!"
    caption_text = caption.upper()
    wrapped_caption = textwrap.fill(caption_text, width=25)
    bbox_c = draw.multiline_textbbox((0, 0), wrapped_caption, font=font_sub)
    w_c, h_c = bbox_c[2] - bbox_c[0], bbox_c[3] - bbox_c[1]
    # Position: Top Center (with some margin)
    draw.multiline_text(((width - w_c)/2, 60), wrapped_caption, font=font_sub, fill="white", stroke_width=3, stroke_fill="black", align="center")

    # --- 4. OVERLAY SUBJECT (Bottom/Template Label) ---
    # Ito yung "Asian Institute of Management..."
    subject_text = subject.upper()
    # multi-line handling para sa long subjects (e.g., 2 or 3 lines max)
    wrapped_subject = textwrap.fill(subject_text, width=70) 
    
    # Apply flexible font scaling logic (Max width = 80% of image width)
    font_scaled_subject = get_flexible_font(draw, wrapped_subject, font_main, width * 0.90)
    
    bbox_s = draw.multiline_textbbox((0, 0), wrapped_subject, font=font_scaled_subject, align="center")
    w_s, h_s = bbox_s[2] - bbox_s[0], bbox_s[3] - bbox_s[1]
    
    # Position: Bottom Center (Mimicking the standard sticker template look)
    # y = height - h_s - 130 means 130px margin from the bottom edge
    x_s = (width - w_s) / 2
    y_s = height - h_s - 65

    # Sticker Label Background
    padding_h = 20 # Horizontal padding para mas mahaba ang box
    padding_v = 10 # Vertical padding para manipis
    draw.rounded_rectangle(
        [x_s - padding_h, y_s - padding_v, x_s + w_s + padding_h, y_s + h_s + padding_v],
        radius=10,
        fill=(255, 255, 255, 255), # Pure White for that sticker feel
        outline=(0, 0, 0),
        width=2
    )
    
    draw.multiline_text((x_s, y_s), wrapped_subject, font=font_scaled_subject, fill="black", align="center")

    img.save(os.path.join("output_images", output_filename))
    return output_filename

def get_flexible_font(draw, text, font_path, max_width, start_size=40):
    """Selyadong Auto-Scale: Binabawasan ang size hanggang mag-kasya"""
    current_size = start_size
    font = ImageFont.truetype(font_path, current_size)
    
    # Habang ang text width ay mas malaki sa max_width, bawasan ang size
    while current_size > 20: # Minimum size limit para mabasa pa rin
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            break
            
        current_size -= 5
        font = ImageFont.truetype(font_path, current_size)
        
    return font



# 4. ENDPOINTS
@app.post("/generate-options")
async def generate_asset_options(request: OptionRequest):
    """Chained AI Workflow: Subject -> Witty Captions -> Visual Prompts -> DALL-E"""
    try:
        audience_str = ", ".join(request.audience_profile)
        # STEP 1: Generate 3 Witty Captions (The "Kanto Wit" Logic)
        text_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a witty Filipino Copywriter"
                        f"Target Audience: {audience_str}. "
                        "Generate 3 punchy, minimalist captions using Taglish slang. "
                        "STRICT: Max 3 words per caption. No punctuation. Newline separated."
                    )
                },
                {"role": "user", "content": f"Subject: {request.subject}\nAudience: {request.audience_profile}"}
            ],
            temperature=0.8
        )
        captions = [c.strip() for c in text_response.choices[0].message.content.split('\n') if len(c) > 1][:3]

        image_results = []
        
        # STEP 2: Recursive Image Generation based on each caption
        for caption in captions:
            # Generate a Visual Prompt inspired by the Caption
            visual_prompt_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a {request.visual_theme} Art Director. Create a DALL-E 3 prompt based on a caption. NO TEXT in the image."
                    },
                    {"role": "user", "content": f"Create a {request.visual_theme} visual for: {request.subject}. Inspired by the phrase: '{caption}'"}
                ]
            )
            
            # THE FIX: Extracting the string content correctly
            final_visual_prompt = visual_prompt_response.choices[0].message.content

            # Call DALL-E 3
            img_res = client.images.generate(
                model="dall-e-3",
                prompt=f"A high-appeal sticker art, neo-pop style, heavy outlines, vibrant: {final_visual_prompt}",
                size="1024x1024"
            )
            
            image_results.append({"caption": caption, "url": img_res.data[0].url})

        return {
            "status": "Selyado Options Ready",
            "images": image_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finalize")
async def finalize_asset(request: FinalizeRequest):
    """Step 3: The Assembly - Combine Art + Subject + Caption"""
    try:
        # 1. Sanitize filename
        clean_name = re.sub(r'[^\w\s-]', '', request.subject).strip().replace(' ', '_')
        output_file = f"STICKER_{clean_name}_{os.urandom(2).hex()}.png"
        
        # 2. THE FIX: Ipasa ang APAT na arguments sa tamang order
        filename = overlay_dual_text_on_image(
            request.image_url,    # 1. image_url
            request.subject,      # 2. subject (YUNG NAWALA!)
            request.caption,      # 3. caption
            output_file           # 4. output_filename
        )
        
        # 3. Save to Mongo
        await captions_collection.insert_one({
            "subject": request.subject,
            "final_caption": request.caption,
            "final_image_path": filename
        })

        # --- THE FIX: DAPAT MERON NITO ---
        return {
            "status": "Success",
            "final_image_url": f"http://localhost:8000/images/{filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)