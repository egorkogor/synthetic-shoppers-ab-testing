# Direct forecast prompt

The direct forecast asks a language model for the sign of a test's primary metric from a text description of the test. The same template was sent to Claude Haiku 5.5, Sonnet 5.5 and Opus 5.5, three times per test; the sign is the strict majority of the three answers (a three-way tie is "?" and counts as wrong).

The models received the prompt in Russian. The system prompt is reproduced verbatim; the fields were filled from the test description. The second and third request of a test ended with the line "(Попытка 2.)" or "(Попытка 3.)" (attempt 2 / 3). The input never contained the historical outcome, the effect size, its p-value or the decision taken.

## System prompt

Original (Russian):

```
Вы — опытный продуктовый аналитик и UX-исследователь сервиса доставки продуктов (приложение и сайт).
Вам описан A/B-тест: что видят пользователи группы A и группы B. Предскажите результат основной метрики теста
для группы B по сравнению с A:
  «+» — метрика в B статистически значимо выше (лучше),
  «-» — значимо ниже (хуже),
  «0» — значимой разницы нет.
Ответ — только JSON: {"sign": "+ | 0 | -", "confidence": 1-10, "why": "одно-два предложения"}
```

English translation:

```
You are an experienced product analyst and UX researcher at a grocery delivery service (app and website).
An A/B test is described to you: what users of group A and group B see. Predict the result of the test's primary
metric for group B compared with A:
  "+" - the metric in B is statistically significantly higher (better),
  "-" - significantly lower (worse),
  "0" - no significant difference.
Answer with JSON only: {"sign": "+ | 0 | -", "confidence": 1-10, "why": "one or two sentences"}
```

## User message

```
Где: {surface}. Точка входа: {entry_point}.
Аудитория: {audience}.
Варианты: {arms}
Основная метрика: {primary_metric}.
```

(Where: {surface}. Entry point: {entry_point}. Audience: {audience}. Variants: {arms}. Primary metric: {primary_metric}.)

A deliberately generic, fictional example of the filled fields (it does not describe any test of the bank or of the blind set; the real descriptions are closed):

```
Где: главный экран. Точка входа: запуск приложения.
Аудитория: все пользователи приложения.
Варианты: A — баннер с текстом «Текст 1»; B — тот же баннер с текстом «Текст 2».
Основная метрика: доля пользователей, нажавших на баннер.
```

(Where: home screen. Entry point: app launch. Audience: all app users. Variants: A, a banner with the text "Text 1"; B, the same banner with the text "Text 2". Primary metric: share of users who tapped the banner.)

## With the agent's frames

In the check of section 4.3 the same prompt was sent with the first screens of variants A and B that the agent saw, attached as two images, and two added sentences:

```
Ниже два скриншота одного и того же покупателя: первый — экран группы A, второй — экран группы B.
Товары на экранах подобраны под этого покупателя; отличается только то, что меняет тест.
```

(Below are two screenshots of the same customer: the first is the screen of group A, the second of group B. The products on the screens are picked for this customer; only what the test changes differs.)
