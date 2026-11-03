# HUB 3I — notas de migração

- Código e referências textuais da marca foram atualizados; nomes de módulos Django (`eucs_platform`) e identificadores de configuração existentes foram preservados para manter compatibilidade.
- Arquivos binários de imagens e PDFs foram preservados sem alteração visual; alguns ainda podem exibir o logotipo/texto antigo e exigem substituição de arte.
- Links externos e endereços de e-mail originais foram preservados para evitar romper integrações; revise-os antes da publicação.
- O arquivo `src/eucs_platform/settings/local.env` contém segredos e foi excluído. Configure um novo arquivo local usando o exemplo e rotacione quaisquer credenciais previamente expostas.
- `.venv`, caches e logs foram excluídos. Recrie o ambiente virtual e instale as dependências do projeto.
- Teste de inicialização Django, migrações, rotas, emails e templates em um ambiente de homologação antes de produção.
