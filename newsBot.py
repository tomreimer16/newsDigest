# https://www.youtube.com/watch?v=1UMHhJEaVTQ

from requests import get
from bs4 import BeautifulSoup
import redis
from secrets import password
import datetime
import time
from json import dumps
import re

class news:
    def __init__(self, url, keywords):
        self.url = url
        self.keywords = keywords
        self.page_response = get(self.url)
        self.page_text = self.page_response.text
        self.db = redis.Redis(host='localhost', port=6379, db=0)

    def parse(self):

        mappings = {
        "BBC" : {"href": "^/news/", "url": "https://www.bbc.co.uk"},
        "Spectator" : {"href": "^/article/", "url": "https://www.spectator.co.uk"}
        }
        
        if "bbc.co.uk" in self.url:
            source = "BBC"
        elif "spectator.co.uk" in self.url:
            source = "Spectator"
        else:
            print("Parser does not know this news source")
            articles=[]

        page_soup = BeautifulSoup(self.page_text, 'html.parser')
        articles = page_soup.find_all( "a", href=re.compile(mappings[source]["href"] ) )
        
        self.saved_links = {}

        for article in articles:
            for keyword in self.keywords:
                if keyword in article.text:
                    if mappings[source]["url"] + article['href'] not in self.saved_links:
                        self.saved_links[article.text] =  mappings[source]["url"] + article['href']

    
    def store(self):
        for link in self.saved_links:
            self.db.set(link, self.saved_links[link] )
            # print("Story:    ", link)
            # print("Link:    ", self.saved_links[link])
            # print("-")

    def email(self):

        linkDict = {}
        for k in self.db.keys():
            linkDict[k] = self.db.get(k)

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
            <h2> %s links you might find interesting today:</h2>

            <ul>
                <li>%s</li>
            </ul>
        """ % (len(linkDict), b'</li><li>'.join([b'<a href="%s">%s' % (value, key) for (key, value) in linkDict.items()]))

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
    urls = ['https://www.bbc.co.uk/news/business',
            'https://www.spectator.co.uk',
            'https://www.bbc.co.uk/news/technology']

    keywords = ['Tesla','Google','Amazon','Apple',
                'Private Equity','Venture Capital',
                'Boris','Sutherland']
    
    for url in urls:
        n = news(url, keywords)
        n.parse()
        n.store()

    if datetime.datetime.now().hour == 13:
        n.email()

if __name__ == "__main__":
    main()
    