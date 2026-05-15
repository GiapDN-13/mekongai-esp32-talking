-- get_news_from_newsnow plugin provider fields
UPDATE ai_model_provider 
SET fields = JSON_ARRAY(
    JSON_OBJECT(
        'key', 'url',
        'type', 'string',
        'label', 'API base URL',
        'default', 'https://newsnow.busiyi.world/api/s?id='
    ),
    JSON_OBJECT(
        'key', 'news_sources',
        'type', 'string',
        'label', 'News sources',
        'default', 'The Paper;Baidu Hot;CLS CN'
    )
)
WHERE provider_code = 'get_news_from_newsnow' 
AND model_type = 'Plugin';
