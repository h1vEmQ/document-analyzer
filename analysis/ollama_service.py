"""
Сервис для работы с Ollama API
"""
import requests
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Сервис для взаимодействия с Ollama API
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        """
        Инициализация сервиса
        
        Args:
            base_url: Базовый URL Ollama API
            model: Модель для использования
        """
        self.base_url = base_url
        self.model = model
        self.generate_url = f"{base_url}/api/generate"
        
    def is_available(self) -> bool:
        """
        Проверяет доступность Ollama сервиса
        
        Returns:
            bool: True если сервис доступен
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"Ollama service not available: {e}")
            return False
    
    def get_available_models(self) -> list:
        """
        Получает список доступных моделей
        
        Returns:
            list: Список моделей
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except requests.RequestException as e:
            logger.error(f"Error getting models: {e}")
            return []
    
    def generate_response(self, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """
        Генерирует ответ от модели
        
        Args:
            prompt: Промпт для модели
            stream: Использовать ли потоковый режим
            
        Returns:
            Dict с ответом модели
        """
        # Настройки для разных моделей
        if self.model.startswith('deepseek'):
            # Для DeepSeek увеличиваем таймаут и настраиваем параметры для русского языка
            timeout = 300  # 5 минут
            options = {
                "temperature": 0.2,  # Более детерминированные ответы для соблюдения языка
                "top_p": 0.7,
                "stop": ["<|end|>", "[/INST]", "Human:", "Assistant:", "English:", "Analysis:", "Summary:"],
                "repeat_penalty": 1.1,  # Снижает повторения
                "num_predict": 2048  # Ограничиваем длину ответа
            }
        else:
            timeout = 120  # 2 минуты
            options = {
                "temperature": 0.5,  # Более детерминированные ответы
                "top_p": 0.8,
                "stop": ["</s>", "<|end|>", "English:", "Analysis:", "Summary:"]
            }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": options
        }
        
        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Парсим JSON ответ от Ollama
                response_data = response.json()
                response_text = response_data.get('response', '')
                
                return {
                    "success": True,
                    "response": response_text,
                    "status_code": response.status_code,
                    "raw_response": response.text
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "status_code": response.status_code
                }
                
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": 0
            }
    
    def compare_documents(self, document1_content: str, document2_content: str, 
                         document1_title: str = "Документ 1", 
                         document2_title: str = "Документ 2") -> Dict[str, Any]:
        """
        Сравнивает два документа с помощью нейросети
        
        Args:
            document1_content: Содержимое первого документа
            document2_content: Содержимое второго документа
            document1_title: Название первого документа
            document2_title: Название второго документа
            
        Returns:
            Dict с результатами сравнения
        """
        # Создаем промпт для сравнения документов
        prompt = self._create_comparison_prompt(
            document1_content, document2_content, document1_title, document2_title
        )
        
        # Получаем ответ от модели
        result = self.generate_response(prompt)
        
        if result["success"]:
            try:
                # Парсим ответ модели
                response_text = result["response"]
                return self._parse_comparison_response(response_text)
            except Exception as e:
                logger.error(f"Error parsing comparison response: {e}")
                return {
                    "success": False,
                    "error": f"Ошибка обработки ответа модели: {e}",
                    "raw_response": result["response"]
                }
        else:
            return result
    
    def _create_comparison_prompt(self, doc1_content: str, doc2_content: str, 
                                 doc1_title: str, doc2_title: str) -> str:
        """
        Создает промпт для сравнения документов
        
        Args:
            doc1_content: Содержимое первого документа
            doc2_content: Содержимое второго документа
            doc1_title: Название первого документа
            doc2_title: Название второго документа
            
        Returns:
            str: Промпт для модели
        """
        # Настройка промпта для разных моделей
        if self.model.startswith('deepseek'):
            system_prompt = "Ты эксперт по анализу документов. КРИТИЧЕСКИ ВАЖНО: Отвечай СТРОГО на русском языке. Никакого английского языка в ответе. Анализируй документы внимательно и структурированно."
        else:
            system_prompt = "Ты эксперт по анализу документов. КРИТИЧЕСКИ ВАЖНО: Отвечай СТРОГО на русском языке. Никакого английского языка в ответе. Сравни два документа и найди различия, сходства и изменения."
        
        prompt = f"""{system_prompt}

ВАЖНО: Ты должен отвечать ТОЛЬКО на русском языке. Никакого английского языка в ответе.

ДОКУМЕНТ 1: "{doc1_title}"
Содержимое:
{doc1_content[:3000]}  # Ограничиваем размер для промпта

ДОКУМЕНТ 2: "{doc2_title}"
Содержимое:
{doc2_content[:3000]}  # Ограничиваем размер для промпта

Пожалуйста, проведи детальное сравнение и предоставь результат в следующем JSON формате. ВСЕ ТЕКСТЫ В JSON ДОЛЖНЫ БЫТЬ НА РУССКОМ ЯЗЫКЕ:

{{
    "summary": "Краткое резюме основных различий",
    "similarities": [
        "Список сходств между документами"
    ],
    "differences": [
        {{
            "type": "content",
            "description": "Описание различия",
            "location": "Место в документе",
            "old_value": "Значение в первом документе",
            "new_value": "Значение во втором документе",
            "significance": "high"
        }}
    ],
    "recommendations": [
        "Рекомендации по изменениям"
    ],
    "overall_assessment": "Общая оценка изменений"
}}

КРИТИЧЕСКИ ВАЖНО: Анализируй документы внимательно и предоставь структурированный результат СТРОГО НА РУССКОМ ЯЗЫКЕ. Никакого английского языка в ответе. Все поля JSON должны содержать только русский текст."""
        
        return prompt
    
    def _parse_comparison_response(self, response_text: str) -> Dict[str, Any]:
        """
        Парсит ответ модели и извлекает структурированные данные
        
        Args:
            response_text: Ответ от модели
            
        Returns:
            Dict с распарсенными данными
        """
        try:
            # Улучшенный парсинг JSON
            json_str = self._extract_json_from_response(response_text)
            
            if json_str:
                # Очищаем JSON от лишних символов
                json_str = json_str.strip()
                parsed_data = json.loads(json_str)
                
                return {
                    "success": True,
                    "comparison_result": parsed_data,
                    "raw_response": response_text
                }
            else:
                # Если JSON не найден, пытаемся создать структурированный ответ
                return self._create_fallback_response(response_text, "comparison")
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.error(f"Сырой ответ: {response_text}")
            
            # Если JSON невалидный, пытаемся исправить
            try:
                fixed_json = self._fix_json_format(json_str)
                if fixed_json:
                    parsed_data = json.loads(fixed_json)
                    return {
                        "success": True,
                        "comparison_result": parsed_data,
                        "raw_response": response_text
                    }
            except:
                pass
            
            # В крайнем случае возвращаем fallback
            return self._create_fallback_response(response_text, "comparison")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при парсинге ответа: {e}")
            return self._create_fallback_response(response_text, "comparison")
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """
        Извлекает JSON из ответа модели
        
        Args:
            response_text: Полный ответ от модели
            
        Returns:
            JSON строка или None
        """
        # Для DeepSeek моделей ищем JSON после тега </think>
        if self.model.startswith('deepseek'):
            # Ищем JSON после тега </think>
            think_end = response_text.find('</think>')
            if think_end != -1:
                json_text = response_text[think_end + 8:]  # +8 для длины '</think>'
            else:
                json_text = response_text
        else:
            json_text = response_text
        
        # Ищем первый { и последний }
        json_start = json_text.find('{')
        json_end = json_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            return json_text[json_start:json_end]
        
        # Если не нашли, ищем в ```json блоках
        json_block_start = json_text.find('```json')
        if json_block_start != -1:
            json_block_start += 7  # длина '```json'
            json_block_end = json_text.find('```', json_block_start)
            if json_block_end != -1:
                json_content = json_text[json_block_start:json_block_end].strip()
                json_start = json_content.find('{')
                json_end = json_content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    return json_content[json_start:json_end]
        
        # Если не нашли, ищем в ``` блоках
        code_block_start = json_text.find('```')
        if code_block_start != -1:
            code_block_start += 3  # длина '```'
            code_block_end = json_text.find('```', code_block_start)
            if code_block_end != -1:
                code_content = json_text[code_block_start:code_block_end].strip()
                json_start = code_content.find('{')
                json_end = code_content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    return code_content[json_start:json_end]
        
        return None
    
    def _fix_json_format(self, json_str: str) -> str:
        """
        Пытается исправить невалидный JSON
        
        Args:
            json_str: Невалидный JSON
            
        Returns:
            Исправленный JSON или None
        """
        try:
            # Убираем лишние символы
            json_str = json_str.strip()
            
            # Убираем комментарии (// и /* */)
            import re
            json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
            
            # Исправляем одинарные кавычки на двойные
            json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
            json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
            
            # Убираем trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            return json_str
        except Exception:
            return None
    
    def _create_fallback_response(self, response_text: str, analysis_type: str) -> Dict[str, Any]:
        """
        Создает fallback ответ, если JSON не удалось распарсить
        
        Args:
            response_text: Ответ от модели
            analysis_type: Тип анализа (comparison, sentiment, key_points)
            
        Returns:
            Структурированный ответ
        """
        if analysis_type == "comparison":
            return {
                "success": True,
                "comparison_result": {
                    "summary": "Анализ выполнен, но результат не в JSON формате",
                    "raw_analysis": response_text,
                    "similarities": [],
                    "differences": [],
                    "recommendations": [],
                    "overall_assessment": "Результат требует ручной проверки"
                },
                "raw_response": response_text
            }
        elif analysis_type == "sentiment":
            return {
                "success": True,
                "sentiment_result": {
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "emotions": [],
                    "summary": "Анализ выполнен, но результат не в JSON формате",
                    "raw_analysis": response_text
                },
                "raw_response": response_text
            }
        elif analysis_type == "key_points":
            return {
                "success": True,
                "key_points_result": {
                    "key_points": [],
                    "summary": "Анализ выполнен, но результат не в JSON формате",
                    "main_topics": [],
                    "raw_analysis": response_text
                },
                "raw_response": response_text
            }
        else:
            return {
                "success": True,
                "result": {
                    "summary": "Анализ выполнен, но результат не в JSON формате",
                    "raw_analysis": response_text
                },
                "raw_response": response_text
            }
    
    def analyze_document_sentiment(self, content: str) -> Dict[str, Any]:
        """
        Анализирует тональность документа
        
        Args:
            content: Содержимое документа
            
        Returns:
            Dict с результатами анализа тональности
        """
        # Настройка промпта для разных моделей
        if self.model.startswith('deepseek'):
            system_prompt = "Ты эксперт по анализу эмоций. КРИТИЧЕСКИ ВАЖНО: Отвечай СТРОГО на русском языке. Никакого английского языка в ответе. Анализируй тональность текста."
        else:
            system_prompt = "КРИТИЧЕСКИ ВАЖНО: Отвечай СТРОГО на русском языке. Никакого английского языка в ответе. Проанализируй тональность и эмоциональную окраску следующего текста:"
        
        prompt = f"""{system_prompt}

ВАЖНО: Ты должен отвечать ТОЛЬКО на русском языке. Никакого английского языка в ответе.

{content[:2000]}

КРИТИЧЕСКИ ВАЖНО: Предоставь результат в JSON формате. ВСЕ ТЕКСТЫ В JSON ДОЛЖНЫ БЫТЬ СТРОГО НА РУССКОМ ЯЗЫКЕ. Никакого английского языка в ответе:
{{
    "sentiment": "positive",
    "confidence": 0.8,
    "emotions": ["довольство", "уверенность"],
    "summary": "краткое описание тональности"
}}"""
        
        result = self.generate_response(prompt)
        
        if result["success"]:
            try:
                response_text = result["response"]
                
                # Для DeepSeek моделей ищем JSON после тега </think>
                if self.model.startswith('deepseek'):
                    # Ищем JSON после тега </think>
                    think_end = response_text.find('</think>')
                    if think_end != -1:
                        json_text = response_text[think_end + 8:]  # +8 для длины '</think>'
                        json_start = json_text.find('{')
                        json_end = json_text.rfind('}') + 1
                    else:
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        json_text = response_text
                else:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_text = response_text
                
                if json_start != -1 and json_end > json_start:
                    json_str = json_text[json_start:json_end]
                    # Очищаем JSON от лишних символов
                    json_str = json_str.strip()
                    parsed_data = json.loads(json_str)
                    
                    return {
                        "success": True,
                        "sentiment_result": parsed_data,
                        "raw_response": response_text
                    }
                else:
                    # Если JSON не найден, создаем fallback ответ
                    return self._create_fallback_response(response_text, "sentiment")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                logger.error(f"Сырой ответ: {response_text}")
                
                # Если JSON невалидный, пытаемся исправить
                try:
                    fixed_json = self._fix_json_format(json_str)
                    if fixed_json:
                        parsed_data = json.loads(fixed_json)
                        return {
                            "success": True,
                            "sentiment_result": parsed_data,
                            "raw_response": response_text
                        }
                except:
                    pass
                
                # В крайнем случае возвращаем fallback
                return self._create_fallback_response(response_text, "sentiment")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при парсинге ответа: {e}")
                return self._create_fallback_response(response_text, "sentiment")
        
        return {
            "success": False,
            "error": "Не удалось проанализировать тональность",
            "raw_response": result.get("response", "")
        }
    
    def extract_key_points(self, content: str) -> Dict[str, Any]:
        """
        Извлекает ключевые моменты из документа
        
        Args:
            content: Содержимое документа
            
        Returns:
            Dict с ключевыми моментами
        """
        # Настройка промпта для разных моделей
        if self.model.startswith('deepseek'):
            system_prompt = "Ты эксперт по извлечению информации. КРИТИЧЕСКИ ВАЖНО: Отвечай СТРОГО на русском языке. Никакого английского языка в ответе. Извлеки ключевые моменты из документа."
        else:
            system_prompt = "КРИТИЧЕСКИ ВАЖНО: Отвечай СТРОГО на русском языке. Никакого английского языка в ответе. Извлеки ключевые моменты из следующего документа:"
        
        prompt = f"""{system_prompt}

ВАЖНО: Ты должен отвечать ТОЛЬКО на русском языке. Никакого английского языка в ответе.

{content[:3000]}

КРИТИЧЕСКИ ВАЖНО: Предоставь результат в JSON формате. ВСЕ ТЕКСТЫ В JSON ДОЛЖНЫ БЫТЬ СТРОГО НА РУССКОМ ЯЗЫКЕ. Никакого английского языка в ответе:
{{
    "key_points": [
        {{
            "point": "ключевой момент",
            "importance": "high",
            "category": "категория"
        }}
    ],
    "summary": "краткое резюме документа",
    "main_topics": ["основные темы"]
}}"""
        
        result = self.generate_response(prompt)
        
        if result["success"]:
            try:
                response_text = result["response"]
                
                # Для DeepSeek моделей ищем JSON после тега </think>
                if self.model.startswith('deepseek'):
                    # Ищем JSON после тега </think>
                    think_end = response_text.find('</think>')
                    if think_end != -1:
                        json_text = response_text[think_end + 8:]  # +8 для длины '</think>'
                        json_start = json_text.find('{')
                        json_end = json_text.rfind('}') + 1
                    else:
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        json_text = response_text
                else:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_text = response_text
                
                if json_start != -1 and json_end > json_start:
                    json_str = json_text[json_start:json_end]
                    # Очищаем JSON от лишних символов
                    json_str = json_str.strip()
                    parsed_data = json.loads(json_str)
                    
                    return {
                        "success": True,
                        "key_points_result": parsed_data,
                        "raw_response": response_text
                    }
                else:
                    # Если JSON не найден, создаем fallback ответ
                    return self._create_fallback_response(response_text, "key_points")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                logger.error(f"Сырой ответ: {response_text}")
                
                # Если JSON невалидный, пытаемся исправить
                try:
                    fixed_json = self._fix_json_format(json_str)
                    if fixed_json:
                        parsed_data = json.loads(fixed_json)
                        return {
                            "success": True,
                            "key_points_result": parsed_data,
                            "raw_response": response_text
                        }
                except:
                    pass
                
                # В крайнем случае возвращаем fallback
                return self._create_fallback_response(response_text, "key_points")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при парсинге ответа: {e}")
                return self._create_fallback_response(response_text, "key_points")
        
        return {
            "success": False,
            "error": "Не удалось извлечь ключевые моменты",
            "raw_response": result.get("response", "")
        }
