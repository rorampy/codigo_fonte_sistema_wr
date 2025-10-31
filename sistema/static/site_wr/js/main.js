
document.addEventListener('DOMContentLoaded', function() {

    //Animação do background de hero-section

    const bgImg1 = document.querySelector('.bg-img-1');
    const bgImg2 = document.querySelector('.bg-img-2');
    
    if (bgImg1 && bgImg2) {
        // Remover animações CSS se existirem
        bgImg1.style.animation = 'none';
        bgImg2.style.animation = 'none';
        
        // Configurar estado inicial
        bgImg1.style.transition = 'opacity 2s ease-in-out';
        bgImg1.style.zIndex = '2';
        bgImg1.style.opacity = '1';
        
        bgImg2.style.zIndex = '1';
        bgImg2.style.opacity = '1'; // Base sempre visível
        
        function fadeBackgroundImages() {
            if (bgImg1.style.opacity === '1' || bgImg1.style.opacity === '') {
                bgImg1.style.opacity = '0'; // Fade out - revela img-2
            } else {
                bgImg1.style.opacity = '1'; // Fade in - cobre img-2
            }
        }
        
        // Alternar a cada 10 segundos
        setInterval(fadeBackgroundImages, 10000);
    }

    // Função que corrige os botões de #marchante #madeireiros
    // Ele recebe um valor de quanto deve scrollar a página até o campo correto
    // Um valor diferente para quando o dispositivo é mobile foi atribuido.


    const profileLinks = document.querySelectorAll('a[href^="#"]');
    
    profileLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');

            const isMobile = window.innerWidth <= 768;
            
            if (href === '#marchantes') {
                e.preventDefault();
                
                const targetElement = document.querySelector(href);
                if (targetElement) {
                    const targetPosition = isMobile ? 1500:1200

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            } else if (href == '#madeireiros'){
                e.preventDefault();

                const targetElement = document.querySelector(href);
                if (targetElement){
                    const targetPosition = isMobile ? 2500:1802

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

});