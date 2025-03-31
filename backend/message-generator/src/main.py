"""
Message Generator for AI Housekeeping Advisor Bot.

This module generates housekeeping advice using Google Vertex AI Gemini API
based on image analysis results and the selected scenario.
"""
import base64
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple, Union

import functions_framework
from flask import Request, jsonify
import google.auth
from google.cloud import aiplatform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_NAME = "gemini-service-account-key"
GEMINI_MODEL_NAME = "gemini-pro"
TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS = 1024
TOP_K = 40
TOP_P = 0.95

PROMPT_TEMPLATES = {
    "plant": """
あなたは植物ケアの専門家です。提供された画像分析結果に基づいて、実用的で具体的な植物のケアアドバイスを提供してください。

画像分析結果:
- 検出されたラベル: {labels}
- 検出されたオブジェクト: {objects}
- 検出されたテキスト: {text}

以下の点を考慮したアドバイスを提供してください：
1. 植物の種類と状態（健康状態、成長段階など）
2. 水やり、日光、肥料に関する具体的なアドバイス
3. 見られる問題（黄色い葉、害虫など）とその解決策
4. 季節に応じたケアのヒント
5. 植物の配置や装飾に関する提案

回答は5つ以内の明確で実行可能なアドバイスにまとめ、箇条書きで提供してください。専門用語は避け、初心者にも理解できる言葉で説明してください。
""",
    "closet": """
あなたは整理収納の専門家です。提供された画像分析結果に基づいて、クローゼットや収納スペースの整理に関する実用的で具体的なアドバイスを提供してください。

画像分析結果:
- 検出されたラベル: {labels}
- 検出されたオブジェクト: {objects}
- 検出されたテキスト: {text}

以下の点を考慮したアドバイスを提供してください：
1. スペースの効率的な活用方法
2. 衣類や小物の分類・整理システム
3. 季節に応じた収納の切り替え方
4. 使いやすさと見た目の美しさを両立させる方法
5. 持続可能な整理整頓の習慣づけ

回答は5つ以内の明確で実行可能なアドバイスにまとめ、箇条書きで提供してください。専門用語は避け、初心者にも理解できる言葉で説明してください。
""",
    "fridge": """
あなたは食品管理と冷蔵庫整理の専門家です。提供された画像分析結果に基づいて、冷蔵庫の整理や食品管理に関する実用的で具体的なアドバイスを提供してください。

画像分析結果:
- 検出されたラベル: {labels}
- 検出されたオブジェクト: {objects}
- 検出されたテキスト: {text}

以下の点を考慮したアドバイスを提供してください：
1. 食品の適切な配置と保存方法
2. 食品の鮮度を保つためのヒント
3. 食品ロスを減らすための工夫
4. 冷蔵庫の清潔さを保つ方法
5. 検出された食材を使った簡単なレシピ提案

回答は5つ以内の明確で実行可能なアドバイスにまとめ、箇条書きで提供してください。専門用語は避け、初心者にも理解できる言葉で説明してください。
"""
}

DEFAULT_ADVICE = """
申し訳ありませんが、提供された画像からは具体的なアドバイスを生成できませんでした。
以下は一般的なハウスキーピングのヒントです：

1. 定期的な整理整頓：週に一度、使用頻度の低いアイテムを整理し、必要なものだけを手の届く場所に保管しましょう。

2. ゾーン分け：スペースをゾーンに分けて、関連するアイテムをまとめて保管することで、探す手間を省きます。

3. ラベリング：収納ボックスやコンテナにラベルを付けると、中身がすぐにわかり、片付けも簡単になります。

4. 「ワンイン・ワンアウト」ルール：新しいアイテムを購入したら、古いアイテムを一つ処分するルールを設けると、物が増えすぎるのを防げます。

5. 5分ルール：毎日5分だけ片付ける習慣をつけると、大掃除の負担が減り、常に整った空間を維持できます。

より具体的なアドバイスが必要な場合は、別の画像をアップロードしてみてください。
"""


def get_credentials():
    """
    Get default credentials for Google Cloud APIs.
    
    Returns:
        None: Uses default credentials from the environment.
        
    Raises:
        Exception: If there's an error getting credentials.
    """
    try:
        logger.info("Using default credentials from environment")
        return None
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        raise


def initialize_vertex_ai() -> None:
    """
    Initialize the Vertex AI client with default credentials.
    
    Raises:
        Exception: If there's an error initializing the Vertex AI client.
    """
    try:
        aiplatform.init()
        
        logger.info("Successfully initialized Vertex AI client")
    except Exception as e:
        logger.error(f"Error initializing Vertex AI client: {str(e)}")
        raise


def format_analysis_result(analysis_result: Dict[str, Any]) -> Dict[str, str]:
    """
    Format the analysis result for inclusion in the prompt.
    
    Args:
        analysis_result: The analysis result from the image processor.
        
    Returns:
        Dict[str, str]: A dictionary containing formatted strings for labels, objects, and text.
    """
    labels_str = ", ".join([f"{label['description']} ({label['score']:.2f})" 
                           for label in analysis_result.get("labels", [])])
    
    objects_str = ", ".join([f"{obj['name']} ({obj['score']:.2f})" 
                            for obj in analysis_result.get("objects", [])])
    
    text_str = analysis_result.get("text", "")
    
    return {
        "labels": labels_str if labels_str else "なし",
        "objects": objects_str if objects_str else "なし",
        "text": text_str if text_str else "なし"
    }


def construct_prompt(scenario: str, analysis_result: Dict[str, Any]) -> str:
    """
    Construct a prompt for the Gemini API based on the scenario and analysis result.
    
    Args:
        scenario: The scenario identifier (plant, closet, or fridge).
        analysis_result: The analysis result from the image processor.
        
    Returns:
        str: The constructed prompt.
        
    Raises:
        ValueError: If the scenario is invalid.
    """
    if scenario not in PROMPT_TEMPLATES:
        raise ValueError(f"Invalid scenario: {scenario}")
    
    formatted_result = format_analysis_result(analysis_result)
    
    prompt = PROMPT_TEMPLATES[scenario].format(
        labels=formatted_result["labels"],
        objects=formatted_result["objects"],
        text=formatted_result["text"]
    )
    
    logger.info(f"Constructed prompt for scenario: {scenario}")
    
    return prompt


def generate_advice(prompt: str) -> Tuple[bool, str, Optional[str]]:
    """
    Generate advice using the Vertex AI Gemini API.
    
    Args:
        prompt: The prompt to send to the Gemini API.
        
    Returns:
        Tuple[bool, str, Optional[str]]: A tuple containing a success flag,
                                        the generated advice or default advice,
                                        and an optional error message.
    """
    try:
        model = aiplatform.GenerativeModel(GEMINI_MODEL_NAME)
        
        generation_config = {
            "temperature": TEMPERATURE,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "top_k": TOP_K,
            "top_p": TOP_P,
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        advice = response.text
        
        logger.info("Successfully generated advice")
        
        return True, advice, None
    except Exception as e:
        logger.error(f"Error generating advice: {str(e)}")
        
        if "safety" in str(e).lower():
            logger.warning("Content blocked due to safety settings, returning default advice")
            return False, DEFAULT_ADVICE, f"Content blocked due to safety settings: {str(e)}"
        
        return False, DEFAULT_ADVICE, f"Error generating advice: {str(e)}"


def validate_request(request_json: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate the request JSON.
    
    Args:
        request_json: The request JSON to validate.
        
    Returns:
        Tuple[bool, Optional[str]]: A tuple containing a boolean indicating if the request is valid,
                                   and an optional error message.
    """
    if not request_json:
        return False, "Request body is empty"
    
    if "scenario" not in request_json:
        return False, "Missing 'scenario' field in request"
    
    if request_json["scenario"] not in PROMPT_TEMPLATES:
        return False, f"Invalid scenario: {request_json['scenario']}. Must be one of: {', '.join(PROMPT_TEMPLATES.keys())}"
    
    if "analysis_result" not in request_json:
        return False, "Missing 'analysis_result' field in request"
    
    return True, None


@functions_framework.http
def generate_message(request: Request) -> Dict[str, Any]:
    """
    Cloud Function entry point for generating messages.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        Dict[str, Any]: A JSON response containing the generated advice or error details.
    """
    logger.info(f"Message generator function invoked with method: {request.method}")
    
    if request.method != "POST":
        logger.error(f"Invalid request method: {request.method}")
        return jsonify({
            "success": False,
            "advice": None,
            "error": "Only POST requests are supported"
        }), 405
    
    try:
        request_json = request.get_json(silent=True)
        
        is_valid, error_message = validate_request(request_json)
        if not is_valid:
            logger.error(f"Invalid request: {error_message}")
            return jsonify({
                "success": False,
                "advice": None,
                "error": error_message
            }), 400
        
        scenario = request_json["scenario"]
        analysis_result = request_json["analysis_result"]
        
        logger.info(f"Processing request for scenario: {scenario}")
        logger.info(f"Analysis result summary: {len(analysis_result.get('labels', []))} labels, "
                   f"{len(analysis_result.get('objects', []))} objects, "
                   f"text length: {len(analysis_result.get('text', ''))}")
        
        get_credentials()
        
        initialize_vertex_ai()
        
        prompt = construct_prompt(scenario, analysis_result)
        
        success, advice, error = generate_advice(prompt)
        
        return jsonify({
            "success": success,
            "advice": advice,
            "error": error
        })
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "success": False,
            "advice": DEFAULT_ADVICE,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "advice": DEFAULT_ADVICE,
            "error": f"Internal server error: {str(e)}"
        }), 500


if __name__ == "__main__":
    from flask import Flask, request as flask_request
    
    app = Flask(__name__)
    
    @app.route("/generate", methods=["POST"])
    def generate():
        return generate_message(flask_request)
    
    app.run(host="0.0.0.0", port=8082, debug=True)
