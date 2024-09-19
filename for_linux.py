from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


app = Flask(__name__)

# Function to get reviews based on ASIN
def get_reviews(asin, output_type='txt'):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")  # Bypass OS security model (useful in Docker)
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument("--disable-gpu")  # Disable GPU for compatibility
    options.add_argument("--remote-debugging-port=9222")  # Avoid DevTools port issues

    service = Service('/var/www/myapp/chromedriver')  

    service.start()
    options.binary_location = '/usr/bin/google-chrome' 
    driver = webdriver.Chrome(service=service, options=options)
    
    # Open the product reviews page
    base_url = f'https://www.amazon.com/product-reviews/{asin}/?pageNumber='
    reviews = []
    max_pages = 10  # You can adjust this to a larger number if needed

    for page in range(1, max_pages + 1):
        driver.get(base_url + str(page))
        time.sleep(10)  # Wait for 10 seconds for manual CAPTCHA solving

        # Extract the reviews, reviewer name, rating, and headline
        review_elements = driver.find_elements(By.CSS_SELECTOR, '.review-text-content span')
        name_elements = driver.find_elements(By.CSS_SELECTOR, '.a-profile-name')
        rating_elements = driver.find_elements(By.CSS_SELECTOR, '.review-rating span.a-icon-alt')
        headline_elements = driver.find_elements(By.CSS_SELECTOR, '.review-title')

        if not review_elements:
            print(f'No more reviews found on page {page}. Stopping...')
            break

        for idx, review_element in enumerate(review_elements):
            review_text = review_element.text
            reviewer_name = name_elements[idx].text if idx < len(name_elements) else "N/A"
            rating = rating_elements[idx].get_attribute("innerHTML") if idx < len(rating_elements) else "N/A"
            headline = headline_elements[idx].text if idx < len(headline_elements) else "N/A"
            
            reviews.append({
                "reviewer_name": reviewer_name,
                "rating": rating,
                "headline": headline,
                "review": review_text
            })

        print(f'Scraped page {page}...')

    # Save the results
    if output_type == 'txt':
        return save_to_txt(asin, reviews)

    driver.quit()

# Function to save reviews to a text file with numbering
def save_to_txt(asin, reviews):
    output_file = f'{asin}_reviews.txt'
    with open(output_file, 'w', encoding='utf-8') as file:
        for idx, review in enumerate(reviews, start=1):
            file.write(f"{idx}.\nReviewer Name: {review['reviewer_name']}\nRating: {review['rating']}\nHeadline: {review['headline']}\nReview: {review['review']}\n\n")
    return output_file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    asin = request.form['asin']
    output_file = get_reviews(asin)
    
    # Send the file as a downloadable attachment
    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run("0.0.0.0",port=8000,debug=True)
