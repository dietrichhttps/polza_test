#!/usr/bin/env python3
"""
Email Validator Tool
Проверяет email-адреса на валидность домена и существование пользователя через SMTP.
"""

import dns.resolver
import smtplib
import socket
import re
import sys
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


class EmailValidator:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        
    def is_valid_email_format(self, email: str) -> bool:
        """Проверяет базовый формат email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def get_domain(self, email: str) -> str:
        """Извлекает домен из email"""
        return email.split('@')[1].lower()
    
    def check_mx_records(self, domain: str) -> Tuple[bool, List[str]]:
        """Проверяет наличие MX-записей для домена"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(mx.exchange).rstrip('.') for mx in mx_records]
            return True, mx_hosts
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return False, []
        except Exception as e:
            print(f"Ошибка при проверке MX для {domain}: {e}")
            return False, []
    
    def check_smtp_user(self, email: str, mx_hosts: List[str]) -> bool:
        """Проверяет существование пользователя через SMTP без отправки письма"""
        for mx_host in mx_hosts:
            try:
                with smtplib.SMTP(mx_host, timeout=self.timeout) as server:
                    server.helo()
                    server.mail('test@example.com')
                    code, message = server.rcpt(email)
                    return code == 250
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError,
                   socket.timeout, socket.gaierror):
                continue
            except Exception:
                continue
        return False
    
    def validate_email(self, email: str) -> Dict[str, str]:
        """Полная валидация email"""
        result = {
            'email': email,
            'status': '',
            'details': ''
        }
        
        if not self.is_valid_email_format(email):
            result['status'] = 'невалидный формат'
            result['details'] = 'Некорректный формат email адреса'
            return result
        
        domain = self.get_domain(email)
        
        has_mx, mx_hosts = self.check_mx_records(domain)
        
        if not has_mx:
            if not mx_hosts:
                result['status'] = 'домен отсутствует'
                result['details'] = f'Домен {domain} не существует'
            else:
                result['status'] = 'MX-записи отсутствуют или некорректны'
                result['details'] = f'Нет MX-записей для домена {domain}'
            return result
        
        result['status'] = 'домен валиден'
        result['details'] = f'Домен {domain} имеет MX-записи: {", ".join(mx_hosts)}'
        
        user_exists = self.check_smtp_user(email, mx_hosts)
        if user_exists:
            result['status'] = 'пользователь существует'
            result['details'] += f'. Пользователь {email} существует'
        else:
            result['details'] += f'. Не удалось проверить существование пользователя'
        
        return result
    
    def validate_emails(self, emails: List[str], max_workers: int = 5) -> List[Dict[str, str]]:
        """Проверяет список email адресов параллельно"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_email = {executor.submit(self.validate_email, email): email 
                             for email in emails}
            
            for future in as_completed(future_to_email):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    email = future_to_email[future]
                    results.append({
                        'email': email,
                        'status': 'ошибка проверки',
                        'details': f'Ошибка при проверке: {str(e)}'
                    })
        
        return results


def main():
    if len(sys.argv) < 2:
        print("Использование: python email_validator.py email1@example.com email2@example.com ...")
        print("Или: python email_validator.py --file emails.txt")
        sys.exit(1)
    
    validator = EmailValidator()
    
    if sys.argv[1] == '--file' and len(sys.argv) > 2:
        try:
            with open(sys.argv[2], 'r', encoding='utf-8') as f:
                emails = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Файл {sys.argv[2]} не найден")
            sys.exit(1)
    else:
        emails = sys.argv[1:]
    
    print(f"Проверка {len(emails)} email адресов...\n")
    
    results = validator.validate_emails(emails)
    
    for result in results:
        print(f"Email: {result['email']}")
        print(f"Статус: {result['status']}")
        print(f"Детали: {result['details']}")
        print("-" * 50)
    
    valid_count = sum(1 for r in results if r['status'] in ['домен валиден', 'пользователь существует'])
    print(f"\nИтого: {valid_count}/{len(results)} адресов прошли базовую проверку")


if __name__ == "__main__":
    main()