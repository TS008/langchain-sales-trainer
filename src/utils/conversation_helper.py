"""
对话助手模块 - 提供实时提示和建议
"""

def get_conversation_tips(messages, persona):
    """
    根据对话历史和客户角色提供实时提示
    """
    if not messages:
        return None
    
    # 获取最近的对话
    recent_messages = messages[-4:] if len(messages) > 4 else messages
    customer_messages = [msg for msg in recent_messages if msg['role'] == 'customer']
    salesperson_messages = [msg for msg in recent_messages if msg['role'] == 'salesperson']
    
    tips = []
    
    # 基于客户类型的提示
    if "预算敏感型" in persona:
        if any("价格" in msg['content'] or "多少钱" in msg['content'] for msg in customer_messages):
            tips.append("💡 客户关注价格，可以强调性价比和保值性")
        if len(salesperson_messages) > 2 and not any("优惠" in msg['content'] or "活动" in msg['content'] for msg in salesperson_messages):
            tips.append("💡 可以适当提及优惠活动或赠品")
    
    elif "追求独特设计型" in persona:
        if any("设计" in msg['content'] or "款式" in msg['content'] for msg in customer_messages):
            tips.append("💡 客户重视设计，可以介绍设计理念和工艺特色")
        if len(salesperson_messages) > 2 and not any("设计师" in msg['content'] or "限量" in msg['content'] for msg in salesperson_messages):
            tips.append("💡 可以强调设计师背景或限量特性")
    
    elif "犹豫不决型" in persona:
        if any("想想" in msg['content'] or "考虑" in msg['content'] for msg in customer_messages):
            tips.append("💡 客户在犹豫，可以提供更多安全感和确认")
        if len(salesperson_messages) > 2:
            tips.append("💡 可以使用二选一法则帮助客户决策")
    
    # 通用提示
    if len(messages) > 6 and not any("试戴" in msg['content'] for msg in salesperson_messages):
        tips.append("💡 可以邀请客户试戴，增加体验感")
    
    if len(messages) > 8 and not any("成交" in msg['content'] or "购买" in msg['content'] for msg in salesperson_messages):
        tips.append("💡 时机成熟，可以尝试推动成交")
    
    return tips

def analyze_conversation_quality(messages):
    """
    分析对话质量，提供改进建议
    """
    if len(messages) < 4:
        return {"score": 0, "suggestions": ["对话轮数太少，无法分析"]}
    
    salesperson_messages = [msg for msg in messages if msg['role'] == 'salesperson']
    customer_messages = [msg for msg in messages if msg['role'] == 'customer']
    
    score = 5  # 基础分数
    suggestions = []
    
    # 检查是否有开放式问题
    question_count = sum(1 for msg in salesperson_messages if '?' in msg['content'] or '吗' in msg['content'])
    if question_count == 0:
        score -= 2
        suggestions.append("建议多使用开放式问题了解客户需求")
    elif question_count >= 2:
        score += 1
    
    # 检查是否有产品推荐
    product_mentions = sum(1 for msg in salesperson_messages if any(word in msg['content'] for word in ['手镯', '款式', '系列', '克重']))
    if product_mentions == 0:
        score -= 1
        suggestions.append("建议具体推荐产品")
    elif product_mentions >= 3:
        score += 1
    
    # 检查客户反应
    positive_reactions = sum(1 for msg in customer_messages if any(word in msg['content'] for word in ['好', '不错', '喜欢', '可以']))
    negative_reactions = sum(1 for msg in customer_messages if any(word in msg['content'] for word in ['不', '算了', '贵', '考虑']))
    
    if positive_reactions > negative_reactions:
        score += 1
    elif negative_reactions > positive_reactions:
        score -= 1
        suggestions.append("客户反应较为消极，建议调整话术")
    
    return {
        "score": max(0, min(10, score)),
        "suggestions": suggestions
    }

def get_next_step_suggestion(messages, persona):
    """
    基于当前对话状态建议下一步行动
    """
    if not messages:
        return "开始与客户打招呼，了解基本需求"
    
    last_customer_msg = None
    for msg in reversed(messages):
        if msg['role'] == 'customer':
            last_customer_msg = msg['content']
            break
    
    if not last_customer_msg:
        return "等待客户回应"
    
    # 基于客户最后的话判断下一步
    if any(word in last_customer_msg for word in ['价格', '多少钱', '贵']):
        return "客户关注价格，建议强调价值和性价比"
    elif any(word in last_customer_msg for word in ['看看', '了解', '介绍']):
        return "客户有兴趣，可以详细介绍产品特色"
    elif any(word in last_customer_msg for word in ['考虑', '想想', '犹豫']):
        return "客户在犹豫，建议提供更多信心支持"
    elif any(word in last_customer_msg for word in ['喜欢', '不错', '好']):
        return "客户反应积极，可以推动试戴或成交"
    else:
        return "继续深入了解客户需求" 