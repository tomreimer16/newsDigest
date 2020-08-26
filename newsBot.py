# https://www.youtube.com/watch?v=1UMHhJEaVTQ

import requests
from bs4 import BeautifulSoup
import redis
from secrets import password
import datetime
import time

class news:
    def __init__(self, url, keywords):
        self.url = url
        self.keywords = keywords
        self.page = requests.get(self.url).text
        self.db = redis.Redis(host='localhost', port=6379, db=0)

    def parse(self):
        soup = BeautifulSoup(self.page, 'html.parser')
        if "bbc.co.uk" in self.url:
            articles = soup.find_all('a',{'href': True})
        elif "news.ycombinator.com" in self.url:
            articles = soup.find_all("a",{"class": "storylink"})
        else:
            print("Parser does not know this news source")
            articles=[]
        self.saved_links = []
        

        for article in articles:
            for keyword in self.keywords:
                if keyword in article.text:
                    self.saved_links.append(article)
    
    def store(self):
        for link in self.saved_links:
            if "bbc.co.uk" in self.url:
                self.db.set(link.text, str(link).replace("href=\"/","href=\"https://www.bbc.co.uk/"))
            else:
                self.db.set(link.text, str(link))

    def email(self):
        links = [self.db.get(k) for k in self.db.keys()]

        # email
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        fromEmail = 'newsDigest16@gmail.com'
        toEmail = 'tomreimer16@gmail.com'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Daily News Digest -- " + str(datetime.date.today())
        msg["From"] = fromEmail
        msg["To"] = toEmail

        html = """
            <h4> %s links you might find interesting today:</h4>
            
            %s
        """ % (len(links), b'<br/><br/>'.join(links).decode())

        mime = MIMEText(html, 'html')

        msg.attach(mime)

        try:
            mail = smtplib.SMTP('smtp.gmail.com', 587)
            mail.ehlo()
            mail.starttls()
            mail.login(fromEmail, password)
            mail.sendmail(fromEmail, toEmail, msg.as_string())
            mail.quit()
            print('Email sent!')
        except Exception as e:
            print('Something went wrong... %s' % e)

        self.db.flushdb()


def main():
    urls = ['https://www.bbc.co.uk/news/business','https://news.ycombinator.com/','https://www.bbc.co.uk/news/technology']
    keywords = ['Tesla','Google','Microsoft','Amazon','Facebook','Apple',
                'Private Equity','Venture Capital']
    
    for url in urls:
        n = news(url, keywords)
        n.parse()
        n.store()

    if datetime.datetime.now().hour == 17:
        n.email()

if __name__ == "__main__":
    main()
    