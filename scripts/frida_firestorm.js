Java.perform(function() {

    function getPassword() {
        console.log("[*] Début de la recherche d'instances de MainActivity...");

        Java.choose('com.pwnsec.firestorm.MainActivity', {

            onMatch: function(instance) {
                console.log("[+] MainActivity instance trouvée : " + instance);

                try {
                    var pass = instance.Password();
                    console.log("[+] Mot de passe Firebase généré : " + pass);
                } catch (e) {
                    console.log("[-] Erreur lors de l'appel de Password() : " + e);
                }
            },

            onComplete: function() {
                console.log("[*] Recherche des instances terminée.");
            }
        });
    }

    console.log("[*] Script chargé. Attente de 3 secondes avant exécution...");
    setTimeout(getPassword, 3000);
});