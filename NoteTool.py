import os
import io
import requests


class Note:
    """生成每条md文件中的笔记"""
    def __init__(self, data):
        self.paperID, self.title, self.authors, self.publisher, self.year, self.url = data
        self.citations, self.information, self.local_link, self.note = "", "", "", ""
        self.pre_deal()

    def pre_deal(self):
        """生成每条论文对应的笔记"""
        # 本地PDF文件超链接
        self.local_link = " [(PDF)]" + f"(./papers/{self.title}.pdf) "
        # 标题加粗
        self.title = f"- **{self.title}.**"
        # 作者斜体
        self.authors = f" *{self.authors}.* "
        # 发表的地方和年份加粗
        self.information = f"**{self.publisher}, {self.year}**"
        # 引用数字黑体
        self.citations = f"[![citation](https://img.shields.io/badge/dynamic/json?label=citation" \
                         f"&query=citationCount&url=https%3A%2F%2Fapi.semanticscholar.org%2Fgraph%2Fv1%2Fpaper%2F" \
                         f"{self.paperID}%3Ffields%3DcitationCount)]({self.url})"
        # 笔记汇总
        self.note = "\r\n" + self.title + self.authors + self.information + self.local_link + self.citations

    def write(self, file):
        """将笔记写入指定文件"""
        with open(file, "a", encoding='utf-8') as f:
            f.write(self.note)
            print("笔记已生成！")


class SemanticScholar:
    def __init__(self, timeout=10):
        self.api_url = "https://api.semanticscholar.org/graph/v1"
        self.timeout = timeout
        self.auth_header = {}

    def get_paperID(self, full_title):
        # 通过doi论文标识获取semanticscholar上的paperId
        if any(i in full_title for i in ["ARXIV",'doi',"DOI"]):
            url = self.api_url + f"/paper/{full_title}"
            return self.get_data(url)['paperId']

        # 通过论文标题搜索，获取semanticscholar上的paperId
        else:
            # 处理输入标题中的非法字符
            for i in ['-', ' ']:
                full_title = full_title.replace(i, '%20')

            url = self.api_url + f"/paper/search?query={full_title}"
            # 从搜索出来的结果中选取第一个作为结果
            return self.get_data(url)['data'][0]['paperId']

    def get_all_information(self, paperID):
        """获取该论文的信息"""
        url = self.api_url + f"/paper/{paperID}?fields=title,venue,year,authors,url"
        r = self.get_data(url)

        title = r['title']
        # Windows文件名中不能包含这些字符
        for i in ['“', '*', '<', '>', '?', r"/", '/', '|', ':']:
            title = title.replace(i, ' ')

        venue = r['venue']
        year  = r['year']
        url = r['url']
        authors = ''
        for author in r['authors']:
            authors += author['name'] + ', '

        return paperID, title, authors[:-2], venue, year, url

    def get_data(self, url):
        return requests.get(url, timeout=self.timeout, headers=self.auth_header).json()


def download_pdf(save_path, pdf_name, pdf_url):
    send_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8"}
    response = requests.get(pdf_url, headers=send_headers)
    bytes_io = io.BytesIO(response.content)
    with open(save_path + f"{pdf_name}.pdf", mode='wb') as f:
        f.write(bytes_io.getvalue())
        print(f'{pdf_name}.pdf,下载成功！')


def rename_file(pdf_path, file_name, new_name):
    file_name = os.path.join(pdf_path, f'{file_name}.pdf')
    new_name = os.path.join(pdf_path, f'{new_name}.pdf')
    if os.path.exists(file_name):
        os.rename(file_name, new_name)
        print("文件名修改成功！")


def is_title(inputs):
    """文件名中的数字大于或等于6个，则判断不是论文标题"""
    num_count = 0
    for i in inputs:
        if i.isdigit():
            num_count += 1
    if num_count >= 6:
        print("该文件名不是论文标题！")
        return False
    return True


if __name__ == '__main__':
    print("------------------------------------------------------------------")
    print("1.（自动下载）输入论文pdf的下载地址（支持arxiv.org自动下载生成笔记）；")
    print("2.（仅生成笔记）输入本地pdf的文件名(确保在papers文件夹下，标题=pdf文件名)；")
    print("3.（仅生成笔记）输入论文标题或DOI；")
    print("------------------------------------------------------------------")
    inputs = input("请选择以上三种方式中的一种进行输入：")

    pdf_path = './papers/'
    note_path = './'

    '''根据inputs，解析到论文标题和pdf文件名'''
    # inputs是pdf的url
    if "http" in inputs:
        # 下载pdf文件
        pdf_url = inputs
        pdf_name = pdf_url.split('/')[-1].replace(".pdf", '')
        download_pdf(pdf_path, pdf_name, pdf_url)

        if "arxiv.org" in inputs:
            title = "ARXIV:{}".format(inputs.split('/')[-1].replace(".pdf", ''))
        else:
            if is_title(inputs):
                title = pdf_name
            else:
                print("该文件名不是论文标题！")
                title = input("请输入该pdf文件的论文标题：")

    # inputs是论文的DOI
    elif any(i in inputs for i in ['doi',"DOI"]):
        print("暂不支持通过DOI下载文件，仅生成笔记！")
        title = inputs
        pdf_name = None

    # inputs是论文标题
    else:
        title = inputs
        pdf_name = inputs.replace(".pdf", '')

    '''title，pdf_name生成notes并规范pdf文件名'''
    sch = SemanticScholar()
    paperID = sch.get_paperID(title)
    inf = sch.get_all_information(paperID)

    # 对不规范的标题重命名
    rename_file(pdf_path, pdf_name, inf[1])

    note = Note(inf)
    note_name = input("请输入保存笔记的文件名（.md后缀会自动添加）：")
    if '.md' not in note_name:
        note_name += '.md'
    note.write(os.path.join(note_path, note_name))