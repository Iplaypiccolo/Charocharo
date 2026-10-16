# 차로차로

마우스, 키보드, 시간에 반응하며 화면 하단에 떠 있는 차로차로 캐릭터.

- 사이트: https://iplaypiccolo.github.io/Charocharo/
- 모션 에디터: https://iplaypiccolo.github.io/Charocharo/editor.html

프로젝트 목적, 동작 원리, 파츠 그림 조건, 에디터 사용법은 [ABOUT.md](ABOUT.md)에 정리되어 있습니다.

## 파일

| 파일 | 역할 |
|---|---|
| `index.html` | 소개 페이지 (캐릭터가 오른쪽 아래에 표시됨) |
| `editor.html` | 파츠·키프레임·반응 규칙을 편집하는 모션 에디터 |
| `charo-pet.js` | 재생기. 캐릭터 파일을 읽어 화면 하단에 띄움 |
| `charo-pet.json` | 캐릭터 파일 (파츠 그림, 동작, 반응 규칙, 표시 설정) |

## 움직임 수정하기

1. 모션 에디터에서 수정 후 **저장 (.json)** 으로 `charo-pet.json` 받기
2. 이 저장소의 `charo-pet.json`을 받은 파일로 덮어쓰기 (Add file → Upload files)
3. 1~2분 뒤 사이트 새로고침

## 다른 사이트에 붙이기

붙일 페이지의 `</body>` 바로 위에 추가:

```html
<script src="https://iplaypiccolo.github.io/Charocharo/charo-pet.js" data-src="https://iplaypiccolo.github.io/Charocharo/charo-pet.json" defer></script>
```

키보드 반응은 키가 눌렸다는 신호만 사용하며, 입력한 글자는 읽거나 저장하지 않습니다.
