class Article:
    """
    An object to pack all the info for an article.
    Nice to have if we extend the logic.
    """

    def __init__(self, author_id, 
                article_title, 
                article_subtitle, 
                article_url, 
                article_claps, 
                read_time, 
                responses, 
                date_created, 
                sections_num, 
                section_titles, 
                paragraphs_num, 
                paragraphs):
        self.author_id = author_id
        self.article_title = article_title 
        self.article_subtitle = article_subtitle 
        self.article_url = article_url 
        self.article_claps = article_claps
        self.read_time = read_time 
        self.responses = responses
        self.date_created = date_created
        self.sections_num = sections_num
        self.section_titles =section_titles
        self.paragraphs_num = paragraphs_num
        self.paragraphs = paragraphs
