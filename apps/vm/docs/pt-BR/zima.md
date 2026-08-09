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

## Comandos

```bash
systemctl --user status vm-zima
podman logs -f vm-zima
qh vm-zima --update --apply
```

## Créditos

[ZimaOS](https://github.com/dockur/zima) — MIT

[Documentação oficial](https://github.com/dockur/zima#readme)
