<template>
  <div class="recipe-cards-panel">
    <p class="recipe-hint">
      🍳 根据识别到的食材，为你推荐以下菜谱，点击选择：
    </p>
    <div class="recipe-cards">
      <button
        v-for="(r, i) in enrichedRecipes"
        :key="i"
        class="recipe-card"
        @click="$emit('select', r)"
      >
        <div class="r-rank">
          <span class="rank-num">{{ i + 1 }}</span>
        </div>
        <div class="r-body">
          <div class="r-header">
            <span class="r-name">{{ r.name }}</span>
            <span v-if="r.time" class="r-time">⏱ {{ r.time }}</span>
            <span v-if="r.difficulty" class="r-diff">{{ r.difficulty }}</span>
          </div>
          <div v-if="r.ingredients.length" class="r-ingredients">
            <span class="ing-label">食材：</span>
            <span v-for="ing in r.ingredients" :key="ing" class="ing-tag">{{ ing }}</span>
          </div>
          <div v-if="r.summary" class="r-summary">{{ r.summary }}</div>
        </div>
      </button>
    </div>
    <button class="btn-skip" @click="$emit('skip')">
      💬 不使用推荐，自由问答
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  recipes: { type: Array, required: true }
})

defineEmits(['select', 'skip'])

function parseRecipe(content) {
  const result = {
    name: '',
    time: '',
    difficulty: '',
    ingredients: [],
    summary: '',
  }

  if (!content) return result

  const lines = content.split('\n')
  let inIngredients = false
  let hasMainIngredients = false

  for (const line of lines) {
    const trimmed = line.trim()

    // 菜名
    if (trimmed.startsWith('菜名：') || trimmed.startsWith('菜名:')) {
      result.name = trimmed.split(/[：:]/, 2)[1]?.trim() || ''
      continue
    }
    // 时间
    if (trimmed.startsWith('烹饪时间：') || trimmed.startsWith('烹饪时间:')) {
      result.time = trimmed.split(/[：:]/, 2)[1]?.trim() || ''
      continue
    }
    // 难度
    if (trimmed.startsWith('难度：') || trimmed.startsWith('难度:')) {
      result.difficulty = trimmed.split(/[：:]/, 2)[1]?.trim() || ''
      continue
    }
    // 主要食材（本地完整菜谱和网络推荐卡片都会出现）
    if (trimmed.startsWith('主要食材：') || trimmed.startsWith('主要食材:')) {
      const ings = trimmed.split(/[：:]/, 2)[1]?.trim() || ''
      result.ingredients = ings.split(/[,，、]/).map(s => s.trim()).filter(Boolean)
      hasMainIngredients = result.ingredients.length > 0
      continue
    }
    // 网络推荐摘要
    if (trimmed.startsWith('简介：') || trimmed.startsWith('简介:')) {
      result.summary = trimmed.split(/[：:]/, 2)[1]?.trim() || ''
      continue
    }
    // 食材清单
    if (trimmed.startsWith('食材清单：') || trimmed.startsWith('食材清单:')) {
      inIngredients = true
      continue
    }
    if (inIngredients && trimmed.startsWith('- ')) {
      const ing = trimmed.slice(2).trim()
      if (ing && !hasMainIngredients) result.ingredients.push(ing)
      continue
    }
    // 遇到烹饪步骤或下一个section就停止收集食材
    if (inIngredients && (
      trimmed.startsWith('烹饪步骤') ||
      trimmed.startsWith('小贴士') ||
      trimmed.startsWith('适合人群') ||
      trimmed === ''
    )) {
      if (trimmed !== '') inIngredients = false
    }

    // summary: 取第一个烹饪步骤作为摘要
    if (!result.summary && trimmed.match(/^\d+\./)) {
      result.summary = trimmed.replace(/^\d+\.\s*/, '')
    }
  }

  return result
}

const enrichedRecipes = computed(() =>
  props.recipes.map(r => {
    const parsed = parseRecipe(r.content)
    return {
      ...r,
      name: r.name || parsed.name || '未知菜谱',
      time: parsed.time,
      difficulty: parsed.difficulty,
      ingredients: parsed.ingredients,
      summary: parsed.summary || r.content.slice(0, 80),
    }
  })
)
</script>

<style scoped>
.recipe-cards-panel {
  margin: 12px 0;
  padding: 16px;
  background: var(--bg-dialog);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
}

.recipe-hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  font-weight: 500;
}

.recipe-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}

.recipe-card {
  display: flex;
  gap: 12px;
  width: 100%;
  padding: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-align: left;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.recipe-card:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-sm);
}

.r-rank {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rank-num {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #fff;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
}

.recipe-card:nth-child(2) .rank-num {
  background: #c9a96e;
}

.recipe-card:nth-child(3) .rank-num {
  background: #b8956a;
}

.r-body {
  flex: 1;
  min-width: 0;
}

.r-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.r-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.r-time {
  font-size: 11px;
  color: var(--text-secondary);
  background: #f0ebe3;
  padding: 1px 8px;
  border-radius: 10px;
}

.r-diff {
  font-size: 11px;
  color: var(--accent);
  background: var(--accent-light);
  padding: 1px 8px;
  border-radius: 10px;
}

.r-ingredients {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  margin-bottom: 6px;
}

.ing-label {
  font-size: 11px;
  color: var(--text-muted);
}

.ing-tag {
  font-size: 11px;
  padding: 1px 8px;
  background: var(--bg-input);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  color: var(--text-secondary);
}

.r-summary {
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.5;
}

.btn-skip {
  width: 100%;
  padding: 8px;
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  border-radius: var(--radius-sm);
  transition: color 0.15s, background 0.15s;
}

.btn-skip:hover {
  color: var(--text-secondary);
  background: var(--hover);
}
</style>
