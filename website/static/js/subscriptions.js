/**
 * @file website's browser side logic subscriptionspage functions
 * @author Ivica Paleka
 */

/*
* * * * * * * * * * * * * * * * * * * * * * * * * * *
* SECTION: Initialization
* * * * * * * * * * * * * * * * * * * * * * * * * * *
*/

/**
 * Call main function upon finished document loading
 *
 */
$(mainSubscriptions);

/**
 * Main function
 * @function mainSite
 *
 */
function mainSubscriptions() {
  $('.checks').click(false);
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    mainSubscriptions
  };
}
