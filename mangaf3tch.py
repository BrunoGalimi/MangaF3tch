from io import BytesIO
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import typer
import requests
import click

hostManga = "https://www.mangaworld.ac/"
app = typer.Typer()

@app.command()
def ping() -> None:
    """Get the ping for the hostManga site"""
    try:
        response = requests.get(hostManga)
        response = click.style(response.status_code, fg="blue", bold=True) if response.status_code == 200 else click.style(response.status_code, fg="red", bold=True)
        typer.echo(f"Ping for url: {hostManga} is : {response}")
    except Exception as e:
        print(e)

@app.command()
def whatami():
    """What is this CLI program"""
    typer.echo(click.style(
        "\nWith this program, you can turn chapters of your favorite manga into a convenient PDF file for offline reading.",
        fg="white"))
    typer.echo(click.style("Key Features:", fg="cyan", bold=True))
    typer.echo(click.style(" - Download images of selected chapters", fg="green"))
    typer.echo(click.style(" - Create an organized, easy-to-read PDF", fg="green"))
    typer.echo(click.style(" - Enjoy your manga offline in one single file", fg="green"))
    typer.echo(click.style(
        "Note: Please ensure you have an active connection to download images and enough space to save the PDF.",
        fg="yellow"))
    typer.echo(click.style("Happy reading!", fg="magenta", bold=True))


@app.command()
def search(
    to_search: str = typer.Argument(..., help="Which manga do you want to search for"),
    limit: int = typer.Argument(10, help="Maximum number of results to return (default: 10)")
) -> None:
    """Search for a manga by keyword and get the manga-code"""
    link_to_search = hostManga + "archive?keyword=" + to_search
    response = requests.get(f"{link_to_search}")
    if response.status_code == 200:
        page_content = response.text
        soup = BeautifulSoup(page_content, 'html.parser')

        paragraphs = soup.find_all('a', class_='manga-title')
        auths_divs = soup.find_all('div', class_='author')
        auths_ctx = []

        for author_div in auths_divs:
            a_tag = author_div.find('a')
            if a_tag:
                auths_ctx.append(a_tag.text.strip())

        if paragraphs:
            # Limit results to the specified number
            for index, paragraph in enumerate(paragraphs[:limit]):
                title = paragraph.text
                href = paragraph.get('href')
                len_link = len(hostManga + "manga/")
                manga_code = href[len_link: len_link + 4].replace('/', '')

                manga_code = click.style(manga_code, fg="yellow", bold=True)
                title = click.style(title, fg="blue", bold=True)

                author_name = auths_ctx[index] if index < len(auths_ctx) else "Unknown Author"
                typer.echo(f"\n • {manga_code}  -  {title}  -  {author_name}")
        else:
            typer.echo("No results found.")
    else:
        typer.echo(click.style(f"error {link_to_search}", fg="red", bold=True))

@app.command()
def getMangaChapter(
        manga_id: int = typer.Argument(..., help = "The manga id. If you don't know what is the id of the manga that are you searching for use \"search\" command"),
        limit: int = typer.Argument(10, help="Maximum number of volume rendered (default: 10)(if 0 see all)")
) -> None:
    link_manga = hostManga + "manga/" + str(manga_id)
    response = requests.get(f"{link_manga}")
    if response.status_code == 200:
        splitted_url = response.url.split("/")
        splitted_url[5] = splitted_url[5].replace("-", " ")
        splitted_url[5] = splitted_url[5].upper()
        typer.echo(click.style(f"\n {splitted_url[5]}", fg="blue", bold=True))
        typer.echo(click.style("\n\n Volumes:", fg="white", bold=True))

        page_content = response.text
        soup = BeautifulSoup(page_content, 'html.parser')
        volume_max = soup.find('p', class_="volume-name d-inline")
        len_volume = volume_max.text.split(' ')[1]
        if len_volume:
            if limit != 0:
                limit = int(len_volume) - limit
            for i in range(int(len_volume), limit, -1):
                i = click.style(i, fg="yellow", bold=True)
                typer.echo(f"\n • Volume {i}")

        inp = -1
        while (inp <= limit and inp != 0) or inp > int(len_volume):
            try:
                inp = int(input("\nWhich volume do you want to see?(0 => exit)\n§ "))
                if (inp <= limit and inp != 0) or inp > int(len_volume):
                    typer.echo(click.style("Insert a valid volume or digit 0 to exit.\n", fg="red", bold=True))
                if inp == 0:
                    break
            except ValueError:
                typer.echo(click.style("Please enter a valid number.\n", fg="red", bold=True))

        desired_index = int(len_volume) - int(inp)
        target_data_index = soup.find('div', class_='volume-chapters', attrs={'data-index': desired_index})

        target_chapter = target_data_index.find_all('div', class_='chapter')
        chaps = []
        for tc in target_chapter: chaps.append(tc.find('a', class_='chap'))

        typer.echo(click.style(f"\n\n Chapters of volume {inp}:", fg="white", bold=True))

        for index, ch in enumerate(chaps):
            i = click.style(index+1, fg="yellow", bold=True)
            typer.echo(f"\n • {i}: {chaps[index].get('title')}")

        inp = -1
        while (inp < 1 and inp != 0) or inp > int(len(chaps)):
            try:
                inp = int(input("\nWhich chapter do you want to download in pdf?(0 => exit)\n§ "))
                if (inp <= 1 and inp != 0) or inp > int(len(chaps)):
                    typer.echo(click.style("Insert a valid volume or digit 0 to exit.\n", fg="red", bold=True))
                if inp == 0:
                    break
            except ValueError:
                typer.echo(click.style("Please enter a valid number.\n", fg="red", bold=True))

        response = requests.get(f"{chaps[inp-1].get('href')}")

        if response.status_code == 200:

            try:
                print("Processing pdf..\n")
                page_content = response.text
                soup = BeautifulSoup(page_content, 'html.parser')

                tot_page = soup.find('select', class_='page custom-select').find('option', value='0')
                tot_page = int(tot_page.text.split('/')[1])

                images = []

                for i in range(1, tot_page + 1):
                    page_url = f"{chaps[inp - 1].get('href')}/{i}"
                    response = requests.get(page_url)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        print(page_url)

                        div_reader = soup.find('div', id='reader')
                        if div_reader:
                            img_tag = div_reader.find('img', class_='img-fluid')
                            if img_tag and img_tag.get('src'):
                                img_url = img_tag.get('src')
                                print(img_url)
                                img_response = requests.get(img_url)

                                if img_response.status_code == 200 and "image" in img_response.headers["Content-Type"]:
                                    try:
                                        img = Image.open(BytesIO(img_response.content))
                                        images.append(img.convert("RGB"))
                                        print(f"Page {i}: Image successfully downloaded")
                                    except Exception as e:
                                        typer.echo(f"Error opening image on page {i}: {e}")
                                else:
                                    typer.echo(f"Error: Content at {img_url} is not a valid image.")
                            else:
                                typer.echo(f"Error: No image found on page {page_url}")
                        else:
                            typer.echo("Error: 'reader' div not found on page")
                    else:
                        typer.echo(f"Connection error for page {page_url}")

                save_images_to_pdf(images, f"{chaps[inp - 1].get('title')}.pdf")
            except Exception as e:
                typer.echo(f"Unexpected error: {e}")




    else:
        typer.echo(click.style(f"error {link_to_search}", fg="red", bold=True))






@app.command()
def getMangaVolume(
        manga_id: int = typer.Argument(..., help = "The manga id. If you don't know what is the id of the manga that are you searching for use \"search\" command"),
        limit: int = typer.Argument(10, help="Maximum number of volume rendered (default: 10)(if 0 see all)"),
        separate_chapters: str = typer.Argument('y', help="If \'y\' save the chapters in different pdf, else if \'n\' save in single pdf (default: y")
) -> None:
    link_manga = hostManga + "manga/" + str(manga_id)
    response = requests.get(f"{link_manga}")
    if response.status_code == 200:
        splitted_url = response.url.split("/")
        splitted_url[5] = splitted_url[5].replace("-", " ")
        splitted_url[5] = splitted_url[5].upper()
        typer.echo(click.style(f"\n {splitted_url[5]}", fg="blue", bold=True))
        typer.echo(click.style("\n\n Volumes:", fg="white", bold=True))

        page_content = response.text
        soup = BeautifulSoup(page_content, 'html.parser')
        volume_max = soup.find('p', class_="volume-name d-inline")
        len_volume = volume_max.text.split(' ')[1]
        if len_volume:
            if limit != 0:
                limit = int(len_volume) - limit
            for i in range(int(len_volume), limit, -1):
                i = click.style(i, fg="yellow", bold=True)
                typer.echo(f"\n • Volume {i}")

        inp = -1
        while (inp <= limit and inp != 0) or inp > int(len_volume):
            try:
                inp = int(input("\nWhich volume do you want to see?(0 => exit)\n§ "))
                if (inp <= limit and inp != 0) or inp > int(len_volume):
                    typer.echo(click.style("Insert a valid volume or digit 0 to exit.\n", fg="red", bold=True))
                if inp == 0:
                    break
            except ValueError:
                typer.echo(click.style("Please enter a valid number.\n", fg="red", bold=True))

        desired_index = int(len_volume) - int(inp)
        target_data_index = soup.find('div', class_='volume-chapters', attrs={'data-index': desired_index})

        target_chapter = target_data_index.find_all('div', class_='chapter')
        chaps = []
        for tc in target_chapter: chaps.append(tc.find('a', class_='chap'))

        images = []
        print(len(chaps))
        for ii in range(len(chaps)-1, -1, -1):
            print("\n"+chaps[ii].get('href')+"\n")

            response = requests.get(f"{chaps[ii].get('href')}")

            if response.status_code == 200:

                try:
                    print("Processing pdf..\n")
                    page_content = response.text
                    soup = BeautifulSoup(page_content, 'html.parser')

                    tot_page = soup.find('select', class_='page custom-select').find('option', value='0')
                    tot_page = int(tot_page.text.split('/')[1])

                    if separate_chapters == 'y':
                        images = []

                    for i in range(1, tot_page + 1):
                        page_url = f"{chaps[ii].get('href')}/{i}"
                        response = requests.get(page_url)

                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            print(page_url)

                            div_reader = soup.find('div', id='reader')
                            if div_reader:
                                img_tag = div_reader.find('img', class_='img-fluid')
                                if img_tag and img_tag.get('src'):
                                    img_url = img_tag.get('src')
                                    print(img_url)
                                    img_response = requests.get(img_url)

                                    if img_response.status_code == 200 and "image" in img_response.headers["Content-Type"]:
                                        try:
                                            img = Image.open(BytesIO(img_response.content))
                                            images.append(img.convert("RGB"))
                                        except Exception as e:
                                            typer.echo(f"Error opening image on page {i}: {e}")
                                    else:
                                        typer.echo(f"Error: Content at {img_url} is not a valid image.")
                                else:
                                    typer.echo(f"Error: No image found on page {page_url}")
                            else:
                                typer.echo("Error: 'reader' div not found on page")
                        else:
                            typer.echo(f"Connection error for page {page_url}")

                    if separate_chapters == 'y':
                        save_images_to_pdf(images, f"{chaps[ii].get('title')}.pdf")

                except Exception as e:
                    typer.echo(f"Unexpected error: {e}")
            else:
                typer.echo(f"Not 200: {response.status_code}")

        if separate_chapters == 'n':
            save_images_to_pdf(images, f"{splitted_url[5]}_vol_{inp}.pdf")



    else:
        typer.echo(click.style(f"error {link_to_search}", fg="red", bold=True))



def save_images_to_pdf(images, output_pdf):
    if images:
        images[0].save(output_pdf, save_all=True, append_images=images[1:])
        print(f"PDF saved successfully as {output_pdf}")
    else:
        print("No images to save.")

if __name__ == "__main__":
    app()
