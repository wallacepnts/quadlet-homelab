# ZimaOS

<img src="https://cdn.jsdelivr.net/gh/dockur/zima@master/assets/20241126-153324.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](../zima.md)**

[< VMs](../../README.pt-BR.md)

ZimaOS — a interface de NAS derivada do CasaOS — sem comprar o hardware.

O ZimaOS em si na **8011**, o visualizador da VM na **8012**. Unit `vm-zima`.

Duas portas, e a diferença importa: a **8011** é a interface web do próprio ZimaOS, a que você usa de verdade, e a **8012** é o visualizador do QEMU, que mostra a tela de boot. Vá na 8011, a não ser que algo não tenha subido.

O que você guardar nele cai no disco virtual, dentro do volume na sua home. O `DISK_SIZE` é o teto; ele cresce conforme o uso em vez de ser tomado de uma vez.

É um sistema de NAS rodando como convidado numa máquina que já tem os seus discos. Serve para experimentar, e é esquisito como lugar onde os arquivos realmente moram.

Todas precisam do `/dev/kvm` no host — sem virtualização por hardware a VM
não sobe ou fica lentíssima. O `RAM_SIZE` é reservado por toda a vida da VM,
então deixe o host respirar; o `DISK_SIZE` é um teto e cresce conforme o uso.

## Instalação

```bash
qh vm-zima
qh vm-zima --apply
```

Instalar a pasta — `qh vm --apply` — traz esta junto com as outras.

## Arquivos

```
vm-zima.container     unit
vm-zima.env.example   ambiente
```

Dados em `~/.config/containers/volumes/vm/zima/storage`.

## Atualizar

```bash
qh vm-zima --update --apply
```

Pinado em `1.7.0`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh vm-zima --backup --apply --out ~/backups
```

O arquivo guarda os diretórios desta unit, os segredos dela e o `.env` próprio — nada que uma irmã também leia.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh vm-zima --restore ~/backups/vm-zima-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `vm-zima` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh vm-zima --remove --apply           # para, mantém os dados
qh vm-zima --remove --purge --apply   # e apaga o volume dela
```

Só os volumes desta VM. O `vm-zima.env` é mantido mesmo sendo lido só por ela —
o purge de uma unit não mexe no arquivo de ambiente.

## Comandos

```bash
systemctl --user status vm-zima
podman logs -f vm-zima
qh vm-zima --update --apply
```

## Créditos

[ZimaOS](https://github.com/dockur/zima) — MIT

[Documentação oficial](https://github.com/dockur/zima#readme)
