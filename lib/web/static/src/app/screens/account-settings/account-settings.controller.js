export function AccountSettingsController(AppApi, UserAccounts, $location, $mdDialog ,$stateParams, $mdToast, $state) {
  console.log($stateParams.accountId)
  var $ctrl = this;
	$ctrl.api_key;
	$ctrl.team_url;
    $ctrl.userAccounts = UserAccounts;
    $ctrl.integration_id = $stateParams.accountId
    $ctrl.submitForm = function(){

		AppApi.submitForm({

		                        'AWS_APIAccessKey': $ctrl.accountDetails.AWS_APIAccessKey,
                                'AWS_APISecretAccess': $ctrl.accountDetails.AWS_APISecretAccess,
                                'integration_id': $stateParams.accountId,


									})
									.then(function(response){
									if(response.status==200){
									    $ctrl.showSimpleToast(response.data);
									    $ctrl.isDisabled = false;}
	                                else{
	                                    $ctrl.returned = "Something went wrong, try again later";
	                                    $ctrl.isDisabled = false;
	                                    }
	                                 });
	}


    $ctrl.goBack = function(){
        $state.go('accountList')
    }

    $ctrl.newUrl = function(){
        AppApi.newUrl({'integration_id':$ctrl.integration_id})
            .then(function(result){
                $ctrl.accountDetails.callback = result.data.callback;
            });
    }

    $ctrl.$onInit = function() {
        AppApi.getUserAccount($stateParams.accountId)
        .then(function (result) {
            $ctrl.userAccounts = result.data;
           console.log($ctrl.userAccounts.is_valid);
        });
      }


    $ctrl.showConfirm = function(ev) {
    var confirm = $mdDialog.confirm()
          .title('Are you sure you want to delete this account?')
          .textContent('Deleting this account will erase all data asscosciated with it!')
          .ariaLabel('Delete Account')
          .targetEvent(ev)
          .ok("Delete")
          .cancel("Cancel");
    $mdDialog.show(confirm).then(function() {
      $ctrl.status = 'We are deleting your account. Please go to accounts page and refresh';
      AppApi.deleteUserAccount($stateParams.accountId)
      });
}

  $ctrl.showSimpleToast = function(data) {
    $mdToast.show(
                     $mdToast.simple()
                        .textContent(data)
                        .hideDelay(10000)
                  )};

}
