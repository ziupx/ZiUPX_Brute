import os
import requests
import concurrent.futures
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.align import Align
from datetime import datetime

console = Console()

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = """
[bold cyan]
███████╗██╗██╗   ██╗██████╗ ██╗  ██╗
╚══███╔╝██║██║   ██║██╔══██╗╚██╗██╔╝
  ███╔╝ ██║██║   ██║██████╔╝ ╚███╔╝ 
 ███╔╝  ██║██║   ██║██╔═══╝  ██╔██╗ 
███████╗██║╚██████╔╝██║     ██╔╝ ██╗
╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝
[/bold cyan]
[bold green]   [+] ZiUPX Smart Brute v1.3[/bold green]
[bold white]   [+] Intelligent Directory Fuzzer (Full Content Saver)[/bold white]
    """
    console.print(Align.center(banner))
    console.print("[bold yellow]═══════════════════════════════════════════════════════════[/bold yellow]\n")

def calibrate(url, headers):
    fake_path = "super-fake-page-123456789"
    test_url = f"{url}/{fake_path}"
    console.print(f"[yellow][*] Калибровка: проверяем {test_url}[/yellow]")
    try:
        response = requests.get(test_url, headers=headers, timeout=5)
        fake_size = len(response.content)
        console.print(f"[green][+] Размер страницы-ошибки: {fake_size} байт.[/green]")
        return fake_size
    except Exception as e:
        console.print(f"[red][!] Ошибка калибровки: {e}[/red]")
        return None

def save_full_content(url, path):
    """Скачивает и сохраняет полный текст файла"""
    # Создаем папку для скачанных файлов, если её нет
    os.makedirs("downloads", exist_ok=True)
    
    # Очищаем имя файла от слешей, чтобы сохранить его на диск
    safe_name = path.replace('/', '_').replace('?', '_').replace('&', '_')
    if not safe_name: 
        safe_name = "index.html"
        
    filepath = os.path.join("downloads", safe_name)
    
    try:
        response = requests.get(url, timeout=5)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)
        return filepath
    except Exception as e:
        return None

def scan_url(url, path, fake_size, headers):
    target_url = f"{url}/{path}"
    try:
        response = requests.get(target_url, headers=headers, timeout=3)
        
        if response.status_code in [200, 301, 302, 403]:
            current_size = len(response.content)
            
            if current_size != fake_size:
                result = {
                    "path": path,
                    "status": response.status_code,
                    "size": current_size,
                    "saved_file": None
                }
                
                # Если код 200, скачиваем полный файл
                if response.status_code == 200:
                    result["saved_file"] = save_full_content(target_url, path)
                    
                return result
    except:
        pass
    return None

def format_size(bytes_size):
    for unit in ['Б', 'КБ', 'МБ']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} ГБ"

def main():
    print_banner()
    console.print("[bold cyan]Введите URL сайта (например, http://testphp.vulnweb.com):[/bold cyan]")
    target_url = input("> ").strip().rstrip('/')
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ZiUPX-Brute/1.3"}

    fake_size = calibrate(target_url, headers)
    if fake_size is None:
        return

    wordlist = [
        "admin", "backup", "config", "test", "api", "login", "db", 
        "wp-admin", "phpmyadmin", "robots.txt", "sitemap.xml", 
        "secret", "hidden", "dev", "private", "uploads", "images", 
        "css", "js", "index.php", "admin.php"
    ]
    
    console.print(f"[yellow][*] Начинаем умный брутфорс ({len(wordlist)} путей)...[/yellow]\n")
    
    found_paths = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn()) as progress:
        task = progress.add_task("[cyan]Поиск директорий...", total=len(wordlist))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(scan_url, target_url, path, fake_size, headers) for path in wordlist]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    found_paths.append(result)
                progress.advance(task)

    console.print("\n")
    if found_paths:
        table = Table(title="[bold green]Найденные скрытые пути[/bold green]", border_style="cyan")
        table.add_column("Путь", style="cyan")
        table.add_column("Код", style="bold")
        table.add_column("Размер", style="white")
        table.add_column("Файл сохранен", style="green")
        
        for item in found_paths:
            status = item["status"]
            if status == 200:
                status_str = f"[bold green]{status}[/bold green]"
            elif status in [301, 302]:
                status_str = f"[bold yellow]{status}[/bold yellow]"
            else:
                status_str = f"[bold red]{status}[/bold red]"
                
            saved = "Да" if item["saved_file"] else "-"
            table.add_row(item["path"], status_str, format_size(item["size"]), saved)
            
        console.print(table)
        
        # Сохранение общего отчета
        filename = f"brute_result_{target_url.replace('http://','').replace('https://','').replace('/','_')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"ZiUPX Smart Brute Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Target: {target_url}\n\n")
            for item in found_paths:
                f.write(f"[{item['status']}] /{item['path']} - {format_size(item['size'])}\n")
                if item["saved_file"]:
                    f.write(f"    Сохранено в: {item['saved_file']}\n")
                
        console.print(f"\n[bold green][✓] Отчет сохранен в файл: {filename}[/bold green]")
        console.print(f"[bold cyan][✓] Полные версии найденных файлов лежат в папке 'downloads/'[/bold cyan]")
        
    else:
        console.print("[bold red][!] Скрытых путей не найдено.[/bold red]")

if __name__ == "__main__":
    main()
