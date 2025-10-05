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
            # Для DeepSeek увеличиваем таймаут и настраиваем параметры
            timeout = 300  # 5 минут
            options = {
                "temperature": 0.3,  # Более детерминированные ответы
                "top_p": 0.8,
                "stop": ["<|end|>", "[/INST]", "Human:", "Assistant:"]
            }
        else:
            timeout = 120  # 2 минуты
            options = {
                "temperature": 0.7,
                "top_p": 0.9,
                "stop": ["</s>", "<|end|>"]
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
            system_prompt = "Ты эксперт по анализу документов. Отвечай ТОЛЬКО на русском языке. Анализируй документы внимательно и структурированно."
        else:
            system_prompt = "Ты эксперт по анализу документов. Ты должен отвечать ТОЛЬКО на русском языке. Сравни два документа и найди различия, сходства и изменения."
        
        prompt = f"""{system_prompt}

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
            "type": "content|structure|format",
            "description": "Описание различия",
            "location": "Место в документе",
            "old_value": "Значение в первом документе",
            "new_value": "Значение во втором документе",
            "significance": "high|medium|low"
        }}
    ],
    "recommendations": [
        "Рекомендации по изменениям"
    ],
    "overall_assessment": "Общая оценка изменений"
}}

Анализируй документы внимательно и предоставь структурированный результат ТОЛЬКО НА РУССКОМ ЯЗЫКЕ."""
        
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
                    "comparison_result": parsed_data,
                    "raw_response": response_text
                }
            else:
                # Если JSON не найден, возвращаем текст как есть
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
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
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
                "raw_response": response_text,
                "parse_error": str(e)
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
            system_prompt = "Ты эксперт по анализу эмоций. Отвечай ТОЛЬКО на русском языке. Анализируй тональность текста."
        else:
            system_prompt = "Ты должен отвечать ТОЛЬКО на русском языке. Проанализируй тональность и эмоциональную окраску следующего текста:"
        
        prompt = f"""{system_prompt}

{content[:2000]}

Предоставь результат в JSON формате. ВСЕ ТЕКСТЫ В JSON ДОЛЖНЫ БЫТЬ НА РУССКОМ ЯЗЫКЕ:
{{
    "sentiment": "positive|negative|neutral",
    "confidence": 0.0-1.0,
    "emotions": ["список эмоций"],
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
                        "sentiment_result": parsed_data
                    }
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in sentiment analysis: {e}")
                logger.error(f"Raw response: {response_text}")
                pass
        
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
            system_prompt = "Ты эксперт по извлечению информации. Отвечай ТОЛЬКО на русском языке. Извлеки ключевые моменты из документа."
        else:
            system_prompt = "Ты должен отвечать ТОЛЬКО на русском языке. Извлеки ключевые моменты из следующего документа:"
        
        prompt = f"""{system_prompt}

{content[:3000]}

Предоставь результат в JSON формате. ВСЕ ТЕКСТЫ В JSON ДОЛЖНЫ БЫТЬ НА РУССКОМ ЯЗЫКЕ:
{{
    "key_points": [
        {{
            "point": "ключевой момент",
            "importance": "high|medium|low",
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
                        "key_points_result": parsed_data
                    }
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in key points extraction: {e}")
                logger.error(f"Raw response: {response_text}")
                pass
        
        return {
            "success": False,
            "error": "Не удалось извлечь ключевые моменты",
            "raw_response": result.get("response", "")
        }
