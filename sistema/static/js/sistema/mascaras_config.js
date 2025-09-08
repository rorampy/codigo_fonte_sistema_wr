$(document).ready(function () {
  // Máscaras fixas
  $('.cpfMask').mask('000.000.000-00');
  $('.cepMask').mask('00000-000');
  $('.cnpjMask').mask('00.000.000/0000-00');
  $('.celular').mask('(00) 00000-0000');
  $('.codBarras').mask('00000.00000 00000.000000 00000.000000 0 00000000000000');
  $('.codAgencia').mask('00000000000');
  $('.codConta').mask('00000000000000000000000000');
  $('.codDigito').mask('00000000');

  function aplicarMascaraCpfCnpj($el) {
    let valor = $el.val().replace(/\D/g, '');
    let mascara = valor.length > 11 ? '00.000.000/0000-00' : '000.000.000-00';
    $el.unmask().mask(mascara);
  }

  $('.cpfCnpj').each(function () {
    aplicarMascaraCpfCnpj($(this));
  });

  $('.cpfCnpj').on('input', function () {
    aplicarMascaraCpfCnpj($(this));
  });
});


document.addEventListener('DOMContentLoaded', function () {
  const input = document.querySelector('#cpfCnpj');
  let cleaveInstance = null;

  function aplicarMascara(valor) {
    const numeros = valor.replace(/\D/g, '');

    if (cleaveInstance) cleaveInstance.destroy();
    if (numeros.length <= 11) {
      cleaveInstance = new Cleave(input, {
        delimiters: ['.', '.', '-'],
        blocks: [3, 3, 3, 2],
        numericOnly: true
      });
    }
    else {
      cleaveInstance = new Cleave(input, {
        delimiters: ['.', '.', '/', '-'],
        blocks: [2, 3, 3, 4, 2],
        numericOnly: true
      });
    }
  }

  aplicarMascara('');

  input.addEventListener('input', () => aplicarMascara(input.value));
});