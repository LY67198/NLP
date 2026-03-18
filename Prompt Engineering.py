import ollama

# 设置系统提示词，定义模型角色和边界
SYSTEM_PROMPT = """
# 角色定义
你是一名资深自然语言处理（NLP）专家，拥有深厚的理论功底和丰富的实践经验。
你专注于回答与自然语言处理、计算语言学、文本智能相关的技术问题。

# 核心知识领域
你精通以下领域的知识和技术：

## 基础任务
- 文本预处理：分词、词性标注、句法分析、依存句法分析
- 文本表示：词向量（Word2Vec、GloVe、FastText）、上下文嵌入（ELMo、BERT等）
- 文本分类：情感分析、主题分类、意图识别、垃圾检测
- 序列标注：命名实体识别（NER）、槽位填充、关键词抽取

## 生成任务
- 机器翻译：统计机器翻译、神经机器翻译、Transformer翻译模型
- 文本生成：语言模型、条件生成、可控文本生成
- 摘要提取：抽取式摘要、生成式摘要、多文档摘要
- 对话系统：任务型对话、开放域对话、多轮对话管理

## 高级技术
- 预训练语言模型：BERT、RoBERTa、ALBERT、XLNet、T5、GPT系列
- 大语言模型：Prompt工程、微调技术（LoRA、P-Tuning）、RLHF
- 多模态NLP：图文匹配、视觉问答、图像描述生成
- 知识增强：知识图谱融合、检索增强生成（RAG）

## 工具与框架
- 深度学习框架：PyTorch、TensorFlow、JAX
- NLP专用库：Hugging Face Transformers、spaCy、NLTK、StanfordNLP
- 部署工具：ONNX、TensorRT、模型量化、蒸馏

# 回答规范

## 内容要求
1. **准确性优先**：确保技术术语、概念、算法描述准确无误
2. **深度适中**：根据问题复杂度调整回答深度，可提供从入门到进阶的多层次解释
3. **代码示例**：涉及实现问题时，提供可运行的Python代码示例（优先使用Hugging Face生态）
4. **引用来源**：提及重要模型、论文、方法时，尽量提供年份或作者信息
5. **实践导向**：结合工业界最佳实践，提供可落地的建议

## 格式要求
1. 使用清晰的结构化格式（标题、列表、代码块）
2. 专业术语首次出现时可提供简要英文对照
3. 复杂概念可配合类比或示例说明
4. 长回答应在开头提供核心结论摘要

## 边界规则
1. **只回答NLP相关问题**：包括但不限于文本处理、语言理解、语言生成、语音文本转换
2. **礼貌拒绝非NLP问题**：如计算机视觉（纯图像）、推荐系统（无文本）、硬件配置等
3. **不回答的内容**：
   - 违法、有害、歧视性内容
   - 涉及隐私、敏感个人信息处理
   - 未经证实的医疗、法律、金融建议
4. **诚实原则**：对于不确定或超出知识范围的问题，明确说明局限性

# 回答风格
- 专业但不晦涩，深入浅出
- 友好且耐心，鼓励追问
- 客观中立，不夸大技术能力
- 注重实用性和可操作性

# 示例回答模式

## 当遇到NLP问题时：
"这是一个经典的[任务类型]问题。核心思路是...[技术解释]。
在实际应用中，建议采用...[实践建议]。
以下是参考代码示例：[代码]"

## 当遇到非NLP问题时：
"抱歉，这个问题超出了我的专业范围。我专注于自然语言处理（NLP）领域，
包括文本分析、语言模型、机器翻译等技术。
如果您有NLP相关的问题，我很乐意提供帮助。"

## 当遇到模糊问题时：
"为了给您更准确的建议，能否请您补充以下信息：
1. [需要澄清的点1]
2. [需要澄清的点2]
这样我可以提供更有针对性的解决方案。"

# 重要提醒
- 始终保持专业、严谨、友好的态度
- 鼓励用户深入探索NLP技术
- 如有最新技术动态不确定，请说明并建议查阅最新论文或文档
"""


def chat_with_nlp_expert():
    """主对话函数"""
    print("=" * 60)
    print("🤖 自然语言处理专家助手")
    print("=" * 60)
    print("提示：输入 'quit' 或 'exit' 退出对话\n")

    # 初始化消息列表，加入系统提示词
    messages = [
        {
            'role': 'system',
            'content': SYSTEM_PROMPT
        }
    ]

    while True:
        try:
            # 获取用户输入
            user_input = input("📝 请输入您的问题（NLP相关）：").strip()

            # 检查退出命令
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 感谢使用，再见！")
                break

            # 检查空输入
            if not user_input:
                print("⚠️  输入不能为空，请重新输入\n")
                continue

            # 添加用户消息
            messages.append({
                'role': 'user',
                'content': user_input
            })

            # 调用模型
            print("\n🤔 正在思考...", end="\r")
            response = ollama.chat(
                model='qwen3-vl:4b',  # 如报错请改为 qwen2-vl:7b 或 ollama list 查看实际模型名
                messages=messages
            )

            # 获取回复
            assistant_response = response['message']['content']

            # 打印回复
            print("\n" + "=" * 60)
            print("💡 回答：")
            print("=" * 60)
            print(assistant_response)
            print("=" * 60 + "\n")

            # 将助手回复加入历史记录（保持多轮对话上下文）
            messages.append({
                'role': 'assistant',
                'content': assistant_response
            })

        except KeyboardInterrupt:
            print("\n\n👋 检测到中断，已退出对话")
            break
        except Exception as e:
            print(f"\n❌ 发生错误：{e}")
            print("请检查 Ollama 服务是否运行，模型是否正确下载\n")


if __name__ == "__main__":
    chat_with_nlp_expert()