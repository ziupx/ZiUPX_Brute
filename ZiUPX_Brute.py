import os
import sys
import requests
import concurrent.futures
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.align import Align
from rich.panel import Panel
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
[bold green]   [+] ZiUPX Smart Brute v1.2[/bold green]
[bold white]   [+] Intelligent Directory Fuzzer (with Content Sniffer)[/bold white]
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

def fetch_content(url):
    """Пытается прочитать первые строки файла, если это текст"""
    try:
        response = requests.get(url, timeout=3)
        # Проверяем, текст ли это (если Content-Type содержит text или json)
        content_type = response.headers.get('Content-Type', '')
        if 'text' in content_type or 'json' in content_type or 'javascript' in content_type:
            # Берем первые 5 строк
            lines = response.text.split('\n')[:5]
            content = '\n'.join(lines)
            if len(content) > 300:
                content = content[:300] + "..."
            return content.strip()
    except:
        pass
    return None

def scan_url(url, path, fake_size, headers):
    target_url = f"{url}/{path}"
    try:
        response = requests.get(target_url, headers=headers, timeout=3)
        
        if response.status_code in [200, 301, 302, 403]:
            current_size = len(response.content)
            
            # УМНАЯ ФИЛЬТРАЦИЯ
            if current_size != fake_size:
                result = {
                    "path": path,
                    "status": response.status_code,
                    "size": current_size,
                    "content": None
                }
                
                # Если код 200, пытаемся прочитать содержимое
                if response.status_code == 200:
                    result["content"] = fetch_content(target_url)
                    
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
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ZiUPX-Brute/1.2"}

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
        
        for item in found_paths:
            status = item["status"]
            if status == 200:
                status_str = f"[bold green]{status}[/bold green]"
            elif status in [301, 302]:
                status_str = f"[bold yellow]{status}[/bold yellow]"
            else:
                status_str = f"[bold red]{status}[/bold red]"
                
            table.add_row(item["path"], status_str, format_size(item["size"]))
            
        console.print(table)
        
        # Вывод содержимого (если оно есть)
        console.print("\n[bold cyan]--- Содержимое найденных файлов (первые строки) ---[/bold cyan]")
        for item in found_paths:
            if item.get("content"):
                console.print(Panel(
                    f"[white]{item['content']}[/white]", 
                    title=f"[bold green]/{item['path']}[/bold green]", 
                    border_style="cyan"
                ))
                
        # Сохранение в файл
        filename = f"brute_result_{target_url.replace('http://','').replace('https://','').replace('/','_')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"ZiUPX Smart Brute Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Target: {target_url}\n\n")
            for item in found_paths:
                f.write(f"[{item['status']}] /{item['path']} - {format_size(item['size'])}\n")
                if item.get("content"):
                    f.write(f"    Content: {item['content'][:100]}...\n")
                
        console.print(f"\n[bold green][✓] Отчет сохранен в файл: {filename}[/bold green]")
        
    else:
        console.print("[bold red][!] Скрытых путей не найдено.[/bold red]")

if __name__ == "__main__":
    main()
