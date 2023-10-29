# danbiTutorial

[깃 레포]
https://github.com/hyewone/danbiTutorial.git


[클라우드 배포]
https://port-0-danbitutorial-be-euegqv2llo6uapzm.sel5.cloudtype.app/swagger/
- 하기 이미지와 같이 Swagger Authorize 인증 후 API 테스트가 가능합니다.
![Untitled](https://www.notion.so/image/https%3A%2F%2Fprod-files-secure.s3.us-west-2.amazonaws.com%2Fa1eed9a8-a823-4016-b506-b2ae59044a8a%2Fe439877a-8ec1-4b27-abbc-858275b8c452%2FUntitled.png?table=block&id=b4a079c0-162d-4f54-9034-a5312e2c2a38&spaceId=a1eed9a8-a823-4016-b506-b2ae59044a8a&width=2000&userId=85e8df52-8e9e-4ff4-88b4-014874a25ef8&cache=v2)


[기타]
https://aerial-dessert-41a.notion.site/6eab1a7090d04f1c9267cf60ad2bd87b?pvs=4


- DB는 local, 클라우드 배포 환경 모두 AWS RDS PostreSQL을 연동했습니다.
- local에서는 env 파일, 클라우드 환경에서는 제공업체의 kubernetes ConfigMap, Secret 기능을 이용했습니다.
- 레포지토리 main 브랜치 머지 시 클라우드 환경으로 간단히 CI/CD 되도록 파이프라인을 구성했습니다.
