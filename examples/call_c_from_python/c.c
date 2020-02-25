#include <stdio.h>
#include "pcm.h"

pin_flist_t *baz(pcm_context_t *ctxp, pin_flist_t *flistp, pin_errbuf_t *ebufp)
{
    printf("In c\n");
    pin_flist_t *output = NULL;
    int status = 1;
    /* input_flist is missing POID, so this should fail */
    PCM_OP(ctxp, PCM_OP_TEST_LOOPBACK, 0, flistp, &output, ebufp);
    if PIN_ERR_IS_ERR(ebufp) {
        output = PIN_FLIST_CREATE(ebufp);
        /* Intentionally forget to reset ebuf */
    }
    PIN_FLIST_FLD_SET(output, PIN_FLD_STATUS, &status, ebufp);
    return output;
}
